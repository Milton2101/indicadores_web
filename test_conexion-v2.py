import os
import time
import warnings
import psycopg2
import pandas as pd
import toml

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

# Conecta a PostgreSQL y devuelve las tablas empaquetadas en un diccionario.
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
        
        # Consulta 1: Vista Diaria
        print("📥 Descargando vista diaria/tiempo real...")
        inicio = time.time()
        df_diario = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.vw_cumplimiento_servicio_tiempo_real LIMIT 100;", 
            conn
        )
        print(f"⏱️  Vista diaria lista en {time.time() - inicio:.2f} segundos.")

        conn.close()
        print("\n🔌 Conexión cerrada con éxito.")
        
        # Guardamos todo en nuestro Diccionario
        diccionario_datos = {
            "diario": df_diario
        }
        
        return diccionario_datos
        
    except Exception as e:
        print(f"\n❌ Ocurrió un error al procesar la base de datos: {e}")
        return None
# if __name__ == "__main__":
print("=== INICIANDO EXTRACCIÓN DE PRUEBA ===")
resultado = extraer_datos_base()
    
    # Comprobamos si pudimos traer la información con éxito
if resultado is not None:
    print("\n📊 ¡Datos en memoria!")
    print(f"Contenido del diccionario: {resultado}")
    print("\nPrimeras filas del DataFrame 'diario':")
    print(resultado["diario"].head(2))