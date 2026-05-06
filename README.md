# Tablero Operativo · Subte de Buenos Aires

## Instalación y ejecución rápida

```bash
# 1. Clonar o copiar los archivos en una carpeta
# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar el dashboard
streamlit run dashboard_subte.py
```

El tablero se abre automáticamente en http://localhost:8501

---

## Estructura del proyecto

```
dashboard_subte.py      ← Script principal (todo en un archivo)
requirements.txt        ← Dependencias Python
README.md               ← Este archivo
```

---

## Conectar a PostgreSQL (pasar de DEMO a producción)

En `dashboard_subte.py`, reemplazá el bloque de carga de datos dentro de `main()`:

```python
# ── ANTES (datos mock) ──
datos = generate_mock_data()

# ── DESPUÉS (PostgreSQL real) ──
import psycopg2
import pandas as pd

@st.cache_data(ttl=120)   # Refresca cada 2 minutos
def cargar_datos_postgres():
    conn_str = (
        "postgresql://USUARIO:PASSWORD@HOST:5432/NOMBRE_BD"
    )
    with psycopg2.connect(conn_str) as conn:
        df_diario = pd.read_sql("""
            SELECT *
            FROM vw_cumplimiento_servicio_tiempo_real
            WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
        """, conn)

        df_semanal = pd.read_sql("""
            SELECT *
            FROM mvw_cumplimiento_semanal
            ORDER BY año_semana DESC
            LIMIT 500000
        """, conn)

        df_mensual = pd.read_sql("""
            SELECT *
            FROM mvw_cumplimiento_mensual
            ORDER BY año_mes DESC
        """, conn)

    return {"diario": df_diario, "semanal": df_semanal, "mensual": df_mensual}

datos = cargar_datos_postgres()
```

### Opción recomendada: variables de entorno con `.streamlit/secrets.toml`

Creá el archivo `.streamlit/secrets.toml`:

```toml
[postgres]
host     = "tu_host"
port     = 5432
dbname   = "tu_base"
user     = "tu_usuario"
password = "tu_password"
```

Y usá `st.secrets["postgres"]` en el código para mayor seguridad.

---

## KPIs monitoreados

| KPI | Descripción | Meta |
|-----|-------------|------|
| Cumplimiento de Servicio | % despachos efectuados / programados | ≥ 90% |
| Índice de Regularidad | Estabilidad de intervalos entre trenes | ≥ 90% |
| Intervalo Medio Efectuado | Tiempo promedio real entre trenes | ≈ Programado |
| Desvío Medio | Dispersión en segundos respecto al intervalo ideal | Mínimo |

---

## Vistas del modelo de datos utilizadas

- `vw_cumplimiento_servicio_tiempo_real` → Vista **Diario / Tiempo Real**
- `mvw_cumplimiento_semanal`            → Vista **Semanal**
- `mvw_cumplimiento_mensual`            → Vista **Mensual**
