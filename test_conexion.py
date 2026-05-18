"""
=============================================================================
  SCRIPT DE DIAGNÓSTICO Y EXTRACCIÓN - SUBTE BA (OPTIMIZADO)
  Prueba de conexión a PostgreSQL y visualización de Diccionarios y DataFrames
=============================================================================
  Este script permite:
    1. Cargar las credenciales reales de tu base de datos desde secrets.toml.
    2. Conectarse a PostgreSQL y traer las 4 vistas analíticas.
    3. Silenciar advertencias de compatibilidad de Pandas.
    4. Medir los tiempos de respuesta de cada consulta SQL.
=============================================================================
"""

import os
import time
import warnings
import psycopg2
import pandas as pd
import toml

# Silenciamos las advertencias de compatibilidad para tener una consola limpia
warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────────────────────────────────────
#  1. FUNCIÓN PARA CARGAR LAS CREDENCIALES (CÓMO FUNCIONA EL SECRETS DE STREAMLIT)
# ─────────────────────────────────────────────────────────────────────────────

def obtener_credenciales_toml():
    """
    Busca el archivo de configuración .streamlit/secrets.toml en la carpeta
    de tu proyecto y extrae las credenciales de PostgreSQL.
    """
    ruta_secretos = os.path.join(".streamlit", "secrets.toml")
    
    if not os.path.exists(ruta_secretos):
        raise FileNotFoundError(
            f"No se encontró el archivo {ruta_secretos}. "
            "Asegúrate de ejecutar el script desde la carpeta raíz de tu proyecto."
        )
    
    secretos = toml.load(ruta_secretos)
    return secretos["postgres"]

# ─────────────────────────────────────────────────────────────────────────────
#  2. EXTRACCIÓN DE DATOS DESDE POSTGRESQL CON CRONÓMETRO
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
        print("✅ ¡Conexión exitosa con la base de datos!\n")
        
        # ── Consulta 1: Vista Diaria ──
        print("📥 Descargando vista diaria/tiempo real...")
        inicio = time.time()
        df_diario = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.vw_cumplimiento_servicio_tiempo_real LIMIT 100;", 
            conn
        )
        print(f"⏱️  Vista diaria lista en {time.time() - inicio:.2f} segundos.")
        
        # ── Consulta 2: Vista Semanal ──
        print("📥 Descargando vista semanal...")
        inicio = time.time()
        df_semanal = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.mvw_cumplimiento_semanal LIMIT 100;", 
            conn
        )
        print(f"⏱️  Vista semanal lista en {time.time() - inicio:.2f} segundos.")
        
        # ── Consulta 3: Vista Mensual ──
        print("📥 Descargando vista mensual...")
        inicio = time.time()
        df_mensual = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.mvw_cumplimiento_mensual LIMIT 100;", 
            conn
        )
        print(f"⏱️  Vista mensual lista en {time.time() - inicio:.2f} segundos.")
        
        # ── Consulta 4: Vista de Frecuencia (Punto Crítico) ──
        # Aquí optimizamos: en vez de un LIMIT global (que confunde a Postgres),
        # le pedimos directamente las frecuencias de una fecha específica para que sea veloz.
        print("📥 Descargando vista de frecuencias (con filtro de fecha para velocidad)...")
        inicio = time.time()
        
        # Primero buscamos qué fecha reciente existe en la tabla para no errar
        try:
            fecha_test_df = pd.read_sql_query(
                "SELECT fecha FROM doo_gco_cisyat.vw_frecuencia_tiempo_real ORDER BY fecha DESC LIMIT 1;",
                conn
            )
            fecha_reciente = fecha_test_df.iloc[0]['fecha'] if not fecha_test_df.empty else '2026-05-15'
        except Exception:
            fecha_reciente = '2026-05-15' # Fallback de seguridad
            
        print(f"   💡 Filtrando frecuencias por la fecha: {fecha_reciente}")
        
        # Hacemos la consulta real filtrando por esa fecha en SQL (¡Mucho más rápido que filtrar en Python!)
        query_frecuencia = f"""
            SELECT * FROM doo_gco_cisyat.vw_frecuencia_tiempo_real 
            WHERE fecha = '{fecha_reciente}'
            LIMIT 200;
        """
        df_frecuencia = pd.read_sql_query(query_frecuencia, conn)
        print(f"⏱️  Vista de frecuencias lista en {time.time() - inicio:.2f} segundos.")
        
        conn.close()
        print("\n🔌 Conexión cerrada con éxito.")
        
        # Guardamos todo en nuestro Diccionario
        diccionario_datos = {
            "diario": df_diario,
            "semanal": df_semanal,
            "mensual": df_mensual,
            "frecuencia": df_frecuencia
        }
        
        return diccionario_datos
        
    except Exception as e:
        print(f"\n❌ Ocurrió un error al procesar la base de datos: {e}")
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
        df_d = datos["diario"]
        print(f"Dimensiones de la tabla (filas, columnas): {df_d.shape}")
        print("Columnas disponibles:")
        print(list(df_d.columns))
        print("\nPrimeras 3 filas de la tabla:")
        print(df_d.head(3))
        
        # Vista de Frecuencias
        print("\n" + "="*80)
        print("📊 DATAFRAME INDEPENDIENTE: FRECUENCIAS (datos['frecuencia'])")
        print("="*80)
        df_f = datos["frecuencia"]
        print(f"Dimensiones de la tabla: {df_f.shape}")
        print("Columnas disponibles:")
        print(list(df_f.columns))
        print("\nPrimeras 3 filas de la tabla:")
        print(df_f.head(3))

    else:
        print("\n❌ No se pudo completar la extracción de datos.")