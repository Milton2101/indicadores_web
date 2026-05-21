import pandas as pd
import psycopg2

def extraer_datos_base():
    try:
        conn = psycopg2.connect(
            host="SBPSSQL",
            port="5050",
            dbname="sbase_gco",
            user="sbase_gco_root",
            password="U9s@rF3#vZq1xL2!"
        )
        print("✅ ¡Conexión exitosa con la base de datos!\n")
        # Consulta 1: Vista Diaria
        print("📥 Descargando vista diaria/tiempo real..."
              )
        df_diario = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.vw_cumplimiento_servicio_tiempo_real LIMIT 100;",
            conn)
        print("⏱️  Vista diaria lista.")
        # print(df_diario)
        conn.close()
        print("\n🔌 Conexión cerrada con éxito.")
        
       # 🚀 RECORTE Y FORMATEO DE LA COLUMNA DE INTERVALOS:
        # Creamos la lista con las columnas que queremos limpiar
        columnas_tiempo = ["intervalo_medio_e_time", "intervalo_medio_p_time"]

        # El bucle agarra una por una y le aplica la misma transformación
        for col in columnas_tiempo:
            df_diario[col] = pd.to_timedelta(df_diario[col])
            df_diario[col] = df_diario[col].apply(
                lambda x: f"{x.components.hours:02d}:{x.components.minutes:02d}:{x.components.seconds:02d}" if pd.notnull(x) else ""
            )
        
        return df_diario
    
    except Exception as e:
        print(f"\n❌ Ocurrió un error al procesar la base de datos: {e}")
        return None
    
    
print("=== INICIANDO EXTRACCIÓN DE PRUEBA ===")
resultado = extraer_datos_base()
print(resultado)