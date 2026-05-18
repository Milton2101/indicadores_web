"""
=============================================================================
  SCRIPT DE DIAGNÓSTICO Y EXTRACCIÓN - SUBTE BA
  Prueba de conexión a PostgreSQL y visualización de Diccionarios y DataFrames
=============================================================================
  Este script permite:
    1. Cargar las credenciales reales de tu base de datos desde secrets.toml.
    2. Conectarse a PostgreSQL y traer las 4 vistas analíticas.
    3. Empaquetar todo en el famoso diccionario 'datos'.
    4. Inspeccionar el diccionario y los DataFrames de forma independiente.
=============================================================================
"""

import os
import psycopg2
import pandas as pd
import toml

# ─────────────────────────────────────────────────────────────────────────────
#  1. FUNCIÓN PARA CARGAR LAS CREDENCIALES (CÓMO FUNCIONA EL SECRETS DE STREAMLIT)
# ─────────────────────────────────────────────────────────────────────────────

def obtener_credenciales_toml():
    """
    Busca el archivo de configuración .streamlit/secrets.toml en la carpeta
    de tu proyecto y extrae las credenciales de PostgreSQL.
    """
    # Definimos la ruta estándar donde Streamlit guarda los secretos
    ruta_secretos = os.path.join(".streamlit", "secrets.toml")
    
    if not os.path.exists(ruta_secretos):
        raise FileNotFoundError(
            f"No se encontró el archivo {ruta_secretos}. "
            "Asegúrate de ejecutar el script desde la carpeta raíz de tu proyecto."
        )
    
    # Leemos el archivo TOML usando la librería 'toml'
    secretos = toml.load(ruta_secretos)
    return secretos["postgres"]

# ─────────────────────────────────────────────────────────────────────────────
#  2. EXTRACCIÓN DE DATOS DESDE POSTGRESQL
# ─────────────────────────────────────────────────────────────────────────────

def extraer_datos_base():
    """Conecta a PostgreSQL y devuelve las tablas empaquetadas en un diccionario."""
    print("🔌 Intentando conectar a PostgreSQL...")
    db_info = obtener_credenciales_toml()
    
    try:
        conn = psycopg2.connect(
            host=db_info["host"],
            port=db_info["port"],
            dbname=db_info["dbname"],
            user=db_info["user"],
            password=db_info["password"]
        )
        print("✅ ¡Conexión exitosa con la base de datos!")
        
        # ── Consulta 1: Vista Diaria ──
        print("📥 Descargando vista diaria/tiempo real...")
        df_diario = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.vw_cumplimiento_servicio_tiempo_real LIMIT 50;", 
            conn
        )
        
        # ── Consulta 2: Vista Semanal ──
        print("📥 Descargando vista semanal...")
        df_semanal = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.mvw_cumplimiento_semanal LIMIT 50;", 
            conn
        )
        
        # ── Consulta 3: Vista Mensual ──
        print("📥 Descargando vista mensual...")
        df_mensual = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.mvw_cumplimiento_mensual LIMIT 50;", 
            conn
        )
        
        # ── Consulta 4: Vista de Frecuencia ──
        print("📥 Descargando vista de frecuencias...")
        df_frecuencia = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.vw_frecuencia_tiempo_real LIMIT 50;",
            conn
        )
        
        conn.close()
        print("🔌 Conexión cerrada con éxito.")
        
        # Guardamos todo en la "bolsa de compras" (el Diccionario)
        diccionario_datos = {
            "diario": df_diario,
            "semanal": df_semanal,
            "mensual": df_mensual,
            "frecuencia": df_frecuencia
        }
        
        return diccionario_datos
        
    except Exception as e:
        print(f"❌ Ocurrió un error al procesar la base de datos: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
#  3. BLOQUE DE EJECUCIÓN E INSPECCIÓN (PRINTS)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== INICIANDO SCRIPT DE PRUEBA DE DATOS ===\n")
    
    # Ejecutamos la extracción
    datos = extraer_datos_base()
    
    if datos is not None:
        # =====================================================================
        #  A. INSPECCIÓN DEL DICCIONARIO COMPLETO
        # =====================================================================
        print("\n" + "="*80)
        print("🔍 INSPECCIÓN DEL DICCIONARIO 'datos'")
        print("="*80)
        print(f"Tipo de objeto principal: {type(datos)}")
        print(f"Llaves disponibles (etiquetas): {list(datos.keys())}")
        
        # Mostramos la estructura interna: qué tipo de dato hay en cada llave
        print("\nEstructura interna del diccionario:")
        for llave, valor in datos.items():
            print(f"  • Llave '{llave}' apunta a un objeto de tipo: {type(valor)} con dimensiones {valor.shape}")

        # =====================================================================
        #  B. INSPECCIÓN DE DATAFRAMES DE FORMA INDEPENDIENTE
        # =====================================================================
        
        # Vista Diaria
        print("\n" + "="*80)
        print("📊 DATAFRAME INDEPENDIENTE: DIARIO (datos['diario'])")
        print("="*80)
        df_d = datos["diario"] # Extraemos el DataFrame de la caja
        print(f"Dimensiones de la tabla (filas, columnas): {df_d.shape}")
        print("Columnas disponibles:")
        print(list(df_d.columns))
        print("\nPrimeras 3 filas de la tabla:")
        print(df_d.head(3)) # .head(3) nos muestra solo las primeras 3 filas para no llenar la pantalla
        
        # Vista Semanal
        print("\n" + "="*80)
        print("📊 DATAFRAME INDEPENDIENTE: SEMANAL (datos['semanal'])")
        print("="*80)
        df_s = datos["semanal"]
        print(f"Dimensiones de la tabla: {df_s.shape}")
        print("Columnas disponibles:")
        print(list(df_s.columns))
        print("\nPrimeras 3 filas de la tabla:")
        print(df_s.head(3))
        
        # =====================================================================
        #  C. ACCESO DIRECTO A UN DATO INDIVIDUAL DE LA BIBLIOTECA
        # =====================================================================
        print("\n" + "="*80)
        print("🧪 PRUEBA DE ACCESO DIRIGIDO")
        print("="*80)
        print("Vamos a acceder a la columna 'linea' directamente desde el diccionario, sin desempaquetar:")
        print("Código ejecutado: datos['diario']['linea'].unique()")
        # .unique() nos dice qué valores distintos (sin repetir) hay en esa columna
        lineas_unicas = datos["diario"]["linea"].unique()
        print(f"Resultado: {lineas_unicas}")

    else:
        print("\n❌ No se pudo completar la extracción de datos.")