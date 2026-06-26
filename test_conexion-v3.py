import pandas as pd
import psycopg2

def extraer_datos_base():
    try:
        conn = psycopg2.connect(
            host="192.168.8.152",
            port="5432",
            dbname="sbase_gco",
            user="postgres",
            password="simon"
        )
        print("✅ ¡Conexión exitosa con la base de datos!\n")
        # Consulta 1: Vista Diaria
        print("📥 Descargando vista diaria/tiempo real..."
              )
        df_diario = pd.read_sql_query(
            "WITH TablaInicial AS (SELECT m.fecha, m.linea, m.sentido, m.hora_solo, m.turno_en_la_hora, m.hora_programada, m.hora_real, m.intervalo_p, m.intervalo_e,m.intervalo_segundos_p, m.intervalo_segundos_e FROM doo_gco_cisyat.mvw_intervalos_ibdo_consolidado m WHERE fecha BETWEEN CURRENT_DATE - 3 AND CURRENT_DATE AND linea = 'A' AND sentido = 'Asc' AND (hora_solo = 8 OR hora_solo = 9)), TablaPromedio AS ( SELECT(AVG(intervalo_segundos_p))::numeric(10,0) AS promedio_p,(AVG(intervalo_segundos_e))::numeric(10,0) AS promedio_eFROM TablaInicial)SELECT promedio_e * '1 second'::interval FROM TablaPromedio;", conn)
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