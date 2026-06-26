import os
import time
import warnings
import psycopg2
import pandas as pd
import toml

# Ignorar advertencias de Pandas sobre conexiones SQL crudas
warnings.filterwarnings('ignore', category=UserWarning)

# Obtengo las credenciales de PostgreSQL desde el archivo .streamlit/secrets.toml
def obtener_credenciales_toml():
    ruta_secretos = os.path.join(".streamlit", "secrets.toml")
    
    if not os.path.exists(ruta_secretos):
        raise FileNotFoundError(
            f"No se encontró el archivo {ruta_secretos}. "
            "Asegúrate de ejecutar el script desde la carpeta raíz de tu proyecto."
        )
    
    secretos = toml.load(ruta_secretos)
    return secretos["postgres"]

# Conecta a PostgreSQL y ejecuta la nueva función
def extraer_datos_base():
    db_info = obtener_credenciales_toml()
    try:
        conn = psycopg2.connect(
            host=db_info["host"],
            port=db_info["port"],
            dbname=db_info["dbname"],
            user=db_info["user"],
            password=db_info["password"]
        )
        print("✅ ¡Conexión exitosa con la base de datos!\n")
        
        print("📥 Descargando datos de la función de rangos personalizados...")
        inicio = time.time()
        
        # 1. Definimos la consulta llamando a la función
        query = """
            SELECT * FROM doo_gco_cisyat.fn_intervalos_rango_personalizado(
                %(fecha_desde)s, %(fecha_hasta)s, %(tipo_dia)s, 
                %(linea)s, %(sentido)s, %(hora_desde)s, %(hora_hasta)s
            );
        """
        
        # 2. Definimos los parámetros de prueba exactos que usamos en SQL
        parametros = {
            "fecha_desde": '2026-06-15',  # Usamos None para que la función interprete como NULL
            "fecha_hasta": '2026-06-15',
            "tipo_dia": 'Feriado',
            "linea": 'A',
            "sentido": 'Asc',
            "hora_desde": 8,
            "hora_hasta": 8
        }
        
        # 3. Ejecutamos pasándole los parámetros a Pandas de forma segura
        df_diario = pd.read_sql_query(query, conn, params=parametros)
        
        print(f"⏱️  Consulta ejecutada y lista en {time.time() - inicio:.2f} segundos.")

        conn.close()
        print("🔌 Conexión cerrada con éxito.\n")
        
        diccionario_datos = {
            "diario": df_diario
        }
        
        return diccionario_datos
        
    except Exception as e:
        print(f"\n❌ Ocurrió un error al procesar la base de datos: {e}")
        return None

# ==========================================
# BLOQUE DE EJECUCIÓN
# ==========================================
print("=== INICIANDO EXTRACCIÓN DE PRUEBA ===")
resultado = extraer_datos_base()
    
# Comprobamos si pudimos traer la información con éxito
if resultado is not None:
    df = resultado["diario"]
    print("📊 ¡Datos en memoria!")
    print(f"Total de registros obtenidos: {len(df)}")
    
    print("\nPrimeras 2 filas del DataFrame:")
    # Mostramos algunas columnas clave para no saturar la consola
    print(df[['hora_programada', 'hora_real', 'tipo_viaje', 'intervalo_segundos_e']].head(2))
    
    # ==========================================
    # CÁLCULOS ESTADÍSTICOS DESDE EL DETALLE
    # ==========================================
    # Filtramos solo los trenes comerciales para que los posicionamientos no sumen al %
    df_comerciales = df[df['tipo_viaje'].isin(['COMPLETO', 'CORTO'])]
    
    # Contamos despachos contando los valores no nulos en las columnas de horario
    programados = df_comerciales['hora_programada'].notna().sum()
    efectuados = df_comerciales['hora_real'].notna().sum()
    
    print(f"\nCantidad de despachos programados: {programados}")
    print(f"Cantidad de despachos efectuados: {efectuados}")
    
    if programados > 0:
        cumplimiento = (efectuados / programados) * 100
        print(f"Cumplimiento de servicio: {cumplimiento:.2f}%")
    else:
        print("Cumplimiento de servicio: N/A (0 programados)")