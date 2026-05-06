"""
=============================================================================
  TABLERO DE CONTROL OPERATIVO - SUBTE DE BUENOS AIRES
  Dashboard de Monitoreo de Desempeño del Servicio
=============================================================================
  Desarrollado con: Streamlit + Plotly
  Autor: Generado como prototipo funcional
  Versión: 1.0

  INSTRUCCIONES DE EJECUCIÓN:
    1. Instalar dependencias:
       pip install streamlit plotly pandas numpy

    2. Ejecutar el dashboard:
       streamlit run dashboard_subte.py

    3. Para conectar a PostgreSQL real, reemplazar la llamada a
       generate_mock_data() por consultas a la base de datos usando
       psycopg2 o SQLAlchemy.
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, timedelta
import random
import psycopg2

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN GLOBAL DE LA PÁGINA
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Subte BA · Tablero Operativo",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  PALETA DE COLORES Y ESTILOS PERSONALIZADOS
# ─────────────────────────────────────────────────────────────────────────────

# Colores oficiales de las líneas del Subte de Buenos Aires
COLORES_LINEAS = {
    "A": "#59B2D8",   # Celeste
    "B": "#E8222C",   # Rojo
    "C": "#0464AB",   # Azul marino
    "D": "#5ABF71",   # Verde
    "E": "#9B5EA4",   # Violeta
    "H": "#F5A623",   # Naranja
    "PreMetro": "#8C7B6E",  # Marrón
}

# Tema del dashboard: control room industrial con fondo oscuro
COLOR_FONDO          = "#0D1117"
COLOR_SUPERFICIE     = "#161B22"
COLOR_BORDE          = "#30363D"
COLOR_TEXTO_PPAL     = "#E6EDF3"
COLOR_TEXTO_SEC      = "#8B949E"
COLOR_ACENTO_VERDE   = "#3FB950"
COLOR_ACENTO_ROJO    = "#F85149"
COLOR_ACENTO_AMBAR   = "#D29922"
COLOR_ACENTO_AZUL    = "#58A6FF"
COLOR_PROGRAMADO     = "#58A6FF"
COLOR_EFECTUADO      = "#3FB950"
COLOR_BTN_SIDEBAR    = "#FF6B35"

CSS_PERSONALIZADO = f"""
<style>
  /* ── Fuentes ── */
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

  /* ── Base de la aplicación ── */
  html, body, .stApp {{
      background-color: {COLOR_FONDO};
      color: {COLOR_TEXTO_PPAL};
      font-family: 'IBM Plex Sans', sans-serif;
  }}

  /* ── Barra lateral ── */
  [data-testid="stSidebar"] {{
      background-color: {COLOR_SUPERFICIE};
      border-right: 1px solid {COLOR_BORDE};
  }}
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMultiSelect label,
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] .stDateInput label {{
      color: {COLOR_TEXTO_SEC} !important;
      font-size: 0.78rem;
      font-family: 'IBM Plex Mono', monospace;
      letter-spacing: 0.06em;
      text-transform: uppercase;
  }}

  /* ── Tarjetas KPI ── */
  .kpi-card {{
      background: {COLOR_SUPERFICIE};
      border: 1px solid {COLOR_BORDE};
      border-radius: 8px;
      padding: 20px 24px;
      position: relative;
      overflow: hidden;
      transition: border-color 0.2s;
  }}
  .kpi-card:hover {{ border-color: {COLOR_ACENTO_AZUL}; }}
  .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: var(--accent-color, {COLOR_ACENTO_AZUL});
      border-radius: 8px 8px 0 0;
  }}
  .kpi-label {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.72rem;
      color: {COLOR_TEXTO_SEC};
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 6px;
  }}
  .kpi-value {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 2.1rem;
      font-weight: 600;
      color: {COLOR_TEXTO_PPAL};
      line-height: 1.1;
  }}
  .kpi-sub {{
      font-size: 0.82rem;
      color: {COLOR_TEXTO_SEC};
      margin-top: 4px;
  }}
  .kpi-delta-pos {{
      font-size: 0.82rem;
      color: {COLOR_ACENTO_VERDE};
      margin-top: 4px;
  }}
  .kpi-delta-neg {{
      font-size: 0.82rem;
      color: {COLOR_ACENTO_ROJO};
      margin-top: 4px;
  }}

  /* ── Encabezado del tablero ── */
  .header-container {{
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px 0 24px 0;
      border-bottom: 1px solid {COLOR_BORDE};
      margin-bottom: 24px;
  }}
  .header-title {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 1.4rem;
      font-weight: 600;
      color: {COLOR_TEXTO_PPAL};
      letter-spacing: 0.02em;
  }}
  .header-subtitle {{
      font-size: 0.82rem;
      color: {COLOR_TEXTO_SEC};
      margin-top: 2px;
  }}
  .status-dot {{
      width: 10px; height: 10px;
      border-radius: 50%;
      background: {COLOR_ACENTO_VERDE};
      box-shadow: 0 0 8px {COLOR_ACENTO_VERDE};
      animation: pulse 2s infinite;
      flex-shrink: 0;
  }}
  @keyframes pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.4; }}
  }}

  /* ── Separadores de sección ── */
  .seccion-titulo {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.78rem;
      color: {COLOR_TEXTO_SEC};
      letter-spacing: 0.12em;
      text-transform: uppercase;
      padding: 12px 0 8px 0;
      border-bottom: 1px solid {COLOR_BORDE};
      margin-bottom: 16px;
  }}

  /* ── Ocultar elementos de Streamlit por defecto ── */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
  
   /* ── Botón colapsar/expandir sidebar ── */
  [data-testid="collapsedControl"] {{
      background-color: {COLOR_BTN_SIDEBAR} !important;
      border-radius: 0 8px 8px 0 !important;
      width: 28px !important;
      height: 52px !important;
      top: 50% !important;
      transform: translateY(-50%) !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      box-shadow: 2px 0 8px rgba(88,166,255,0.35) !important;
      transition: background-color 0.2s, box-shadow 0.2s !important;
  }}
  [data-testid="collapsedControl"]:hover {{
      background-color: {COLOR_ACENTO_VERDE} !important;
      box-shadow: 2px 0 12px rgba(63,185,80,0.45) !important;
  }}
  [data-testid="collapsedControl"] svg {{
      fill: {COLOR_FONDO} !important;
      width: 16px !important;
      height: 16px !important;
  }}
  
  /* ── Widgets de Streamlit ── */
  .stSelectbox > div > div,
  .stMultiSelect > div > div {{
      background-color: {COLOR_FONDO} !important;
      border-color: {COLOR_BORDE} !important;
      color: {COLOR_TEXTO_PPAL} !important;
  }}
</style>
"""

st.markdown(CSS_PERSONALIZADO, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  CONEXIÓN A POSTGRES
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # La caché dura 5 minutos (300 segundos). Así no saturamos la base.
def get_postgres_data():
    """Conecta a PostgreSQL y trae los datos de las vistas optimizadas."""
    
    # 1. Leer las credenciales del archivo secrets.toml
    db_info = st.secrets["postgres"]
    
    # 2. Armar la conexión
    try:
        conn = psycopg2.connect(
            host=db_info["host"],
            port=db_info["port"],
            dbname=db_info["dbname"],
            user=db_info["user"],
            password=db_info["password"]
        )
        
        # 3. Consultar las vistas directamente usando Pandas
        # Como las vistas ya están hiper optimizadas, podemos hacer SELECT *
        df_diario = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.vw_cumplimiento_servicio_tiempo_real;", 
            conn
        )
        
        df_semanal = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.mvw_cumplimiento_semanal;", 
            conn
        )
        
        df_mensual = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.mvw_cumplimiento_mensual;", 
            conn
        )
        
        df_frecuencia = pd.read_sql_query(
            "SELECT * FROM doo_gco_cisyat.vw_frecuencia_tiempo_real;",
            conn
        )
        
        conn.close()
        
        return {
            "diario": df_diario,
            "semanal": df_semanal,
            "mensual": df_mensual,
            "frecuencia": df_frecuencia
        }
        
    except Exception as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return {"diario": pd.DataFrame(), "semanal": pd.DataFrame(), "mensual": pd.DataFrame(), "frecuencia": pd.DataFrame()}


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS: FORMATO Y CÁLCULO
# ─────────────────────────────────────────────────────────────────────────────

def seg_a_minutos_segundos(segundos: float) -> str:
    """Convierte segundos a formato 'Xm Ys'."""
    seg = int(segundos)
    return f"{seg // 60}m {seg % 60:02d}s"

def color_kpi(valor: float, umbral_ok: float = 0.90, umbral_warn: float = 0.75) -> str:
    """Devuelve el color de acento según el valor de un KPI proporcional."""
    if valor >= umbral_ok:
        return COLOR_ACENTO_VERDE
    elif valor >= umbral_warn:
        return COLOR_ACENTO_AMBAR
    return COLOR_ACENTO_ROJO

def render_kpi_card(label: str, value: str, sub: str = "",
                    delta: str = "", delta_pos: bool = True,
                    accent: str = COLOR_ACENTO_AZUL):
    """Renderiza una tarjeta KPI con HTML personalizado."""
    delta_class = "kpi-delta-pos" if delta_pos else "kpi-delta-neg"
    delta_html  = f'<div class="{delta_class}">{delta}</div>' if delta else ""
    sub_html    = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card" style="--accent-color: {accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {sub_html}
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN PLOTLY: TEMA OSCURO CORPORATIVO
# ─────────────────────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=COLOR_SUPERFICIE,
    font=dict(family="IBM Plex Mono, monospace", color=COLOR_TEXTO_SEC, size=11),
    xaxis=dict(
        gridcolor=COLOR_BORDE, linecolor=COLOR_BORDE,
        tickfont=dict(size=10), zeroline=False,
    ),
    yaxis=dict(
        gridcolor=COLOR_BORDE, linecolor=COLOR_BORDE,
        tickfont=dict(size=10), zeroline=False,
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", bordercolor=COLOR_BORDE,
        borderwidth=1, orientation="h",
        yanchor="bottom", y=1.02, xanchor="right", x=1,
    ),
    margin=dict(l=10, r=10, t=40, b=10),
    hoverlabel=dict(
        bgcolor=COLOR_SUPERFICIE, bordercolor=COLOR_BORDE,
        font=dict(family="IBM Plex Mono", color=COLOR_TEXTO_PPAL, size=12),
    ),
)

# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICOS
# ─────────────────────────────────────────────────────────────────────────────

def grafico_intervalos(df: pd.DataFrame, eje_x: str, titulo: str) -> go.Figure:
    """
    Gráfico de líneas doble: Intervalo Efectuado vs Programado.
    Agrupa por eje_x y promedia los intervalos.
    """
    agg = (df.groupby(eje_x, as_index=False)
             .agg(
                 ie=("intervalo_medio_e_sec", "mean"),
                 ip=("intervalo_promedio_programado", "mean"),
             )
             .sort_values(eje_x))

    agg["ie_fmt"] = agg["ie"].apply(seg_a_minutos_segundos)
    agg["ip_fmt"] = agg["ip"].apply(seg_a_minutos_segundos)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg[eje_x], y=agg["ie"],
        mode="lines+markers",
        name="Intervalo Efectuado",
        line=dict(color=COLOR_EFECTUADO, width=2.5),
        marker=dict(size=5, color=COLOR_EFECTUADO),
        hovertemplate="<b>%{x}</b><br>Efectuado: %{customdata}<extra></extra>",
        customdata=agg["ie_fmt"],
    ))
    fig.add_trace(go.Scatter(
        x=agg[eje_x], y=agg["ip"],
        mode="lines+markers",
        name="Intervalo Programado",
        line=dict(color=COLOR_PROGRAMADO, width=2, dash="dot"),
        marker=dict(size=4, color=COLOR_PROGRAMADO),
        hovertemplate="<b>%{x}</b><br>Programado: %{customdata}<extra></extra>",
        customdata=agg["ip_fmt"],
    ))

    # Área de diferencia sombreada
    x_combined = list(agg[eje_x]) + list(agg[eje_x])[::-1]
    y_fill     = list(agg["ie"])  + list(agg["ip"])[::-1]
    fig.add_trace(go.Scatter(
        x=x_combined, y=y_fill,
        fill="toself",
        fillcolor="rgba(248, 81, 73, 0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip", showlegend=False,
        name="Desvío",
    ))

    layout = PLOTLY_LAYOUT.copy()
    layout.update(
        title=dict(text=titulo, font=dict(size=13, color=COLOR_TEXTO_PPAL), x=0),
        yaxis=dict(**PLOTLY_LAYOUT["yaxis"], title="segundos"),
        height=320,
    )
    fig.update_layout(**layout)
    return fig


def grafico_despachos(df: pd.DataFrame, eje_x: str, titulo: str) -> go.Figure:
    """
    Gráfico de barras agrupadas: Despachos Programados vs Efectuados.
    """
    agg = (df.groupby(eje_x, as_index=False)
             .agg(
                 prog=("despachos_programados", "sum"),
                 efec=("despachos_efectuados", "sum"),
             )
             .sort_values(eje_x))

    agg["cumpl"] = (agg["efec"] / agg["prog"]).clip(0, 1)
    agg["cumpl_pct"] = (agg["cumpl"] * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg[eje_x], y=agg["prog"],
        name="Programados",
        marker_color=COLOR_PROGRAMADO,
        opacity=0.5,
        hovertemplate="<b>%{x}</b><br>Programados: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=agg[eje_x], y=agg["efec"],
        name="Efectuados",
        marker_color=COLOR_EFECTUADO,
        hovertemplate=(
            "<b>%{x}</b><br>Efectuados: %{y:,}<br>"
            "Cumpl.: %{customdata:.1f}%<extra></extra>"
        ),
        customdata=agg["cumpl_pct"],
    ))

    layout = PLOTLY_LAYOUT.copy()
    layout.update(
        title=dict(text=titulo, font=dict(size=13, color=COLOR_TEXTO_PPAL), x=0),
        barmode="overlay",
        yaxis=dict(**PLOTLY_LAYOUT["yaxis"], title="despachos"),
        height=320,
    )
    fig.update_layout(**layout)
    return fig


def grafico_regularidad(df: pd.DataFrame, eje_x: str, titulo: str) -> go.Figure:
    """
    Gráfico de área del Índice de Regularidad a lo largo del tiempo.
    Incluye una banda de referencia para la meta (90%).
    """
    agg = (df.groupby(eje_x, as_index=False)
             .agg(reg=("indice_regularidad", "mean"))
             .sort_values(eje_x))

    agg["reg_pct"] = (agg["reg"] * 100).round(2)

    # Color dinámico por punto según umbral
    colores_puntos = [
        COLOR_ACENTO_VERDE if v >= 0.90
        else (COLOR_ACENTO_AMBAR if v >= 0.75 else COLOR_ACENTO_ROJO)
        for v in agg["reg"]
    ]

    fig = go.Figure()

    # Línea de meta
    fig.add_hline(
        y=90, line_dash="dot",
        line_color=COLOR_ACENTO_AMBAR,
        opacity=0.6,
        annotation_text="Meta 90%",
        annotation_font=dict(color=COLOR_ACENTO_AMBAR, size=10),
        annotation_position="bottom right",
    )

    # Área rellena
    fig.add_trace(go.Scatter(
        x=agg[eje_x], y=agg["reg_pct"],
        fill="tozeroy",
        fillcolor="rgba(63, 185, 80, 0.12)",
        mode="lines+markers",
        name="Regularidad",
        line=dict(color=COLOR_ACENTO_VERDE, width=2.5),
        marker=dict(size=6, color=colores_puntos),
        hovertemplate="<b>%{x}</b><br>Regularidad: %{y:.1f}%<extra></extra>",
    ))

    layout = PLOTLY_LAYOUT.copy()
    layout.update(
        title=dict(text=titulo, font=dict(size=13, color=COLOR_TEXTO_PPAL), x=0),
        yaxis=dict(**PLOTLY_LAYOUT["yaxis"], title="%", range=[0, 105]),
        height=300,
    )
    fig.update_layout(**layout)
    return fig


def grafico_mapa_calor_linea(df: pd.DataFrame) -> go.Figure:
    """
    Heatmap: Cumplimiento por hora del día y línea.
    Útil para identificar de un vistazo qué línea/hora tiene problemas.
    """
    agg = (df.groupby(["linea", "hora_solo"], as_index=False)
             .agg(cumpl=("cumplimiento_servicio", "mean")))

    pivot = agg.pivot(index="linea", columns="hora_solo", values="cumpl")

    # Orden de líneas para el heatmap
    orden_lineas = [l for l in ["A", "B", "C", "D", "E", "H", "PreMetro"]
                    if l in pivot.index]
    pivot = pivot.loc[orden_lineas]

    text_vals = pivot.map(lambda v: f"{v*100:.0f}%" if pd.notna(v) else "")

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"{h}:00" for h in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[
            [0.00, "#F85149"],
            [0.50, "#D29922"],
            [0.80, "#3FB950"],
            [1.00, "#3FB950"],
        ],
        zmin=0.6, zmax=1.0,
        text=text_vals.values,
        texttemplate="%{text}",
        textfont=dict(size=9, family="IBM Plex Mono"),
        hovertemplate="Línea %{y} · %{x}<br>Cumplimiento: %{z:.1%}<extra></extra>",
        showscale=True,
        colorbar=dict(
            title="Cumpl.",
            tickformat=".0%",
            thickness=12,
            len=0.8,
            bgcolor="rgba(0,0,0,0)",
            bordercolor=COLOR_BORDE,
            tickfont=dict(color=COLOR_TEXTO_SEC, size=9),
        ),
    ))

    layout = PLOTLY_LAYOUT.copy()
    layout.update(
        title=dict(
            text="Mapa de Calor · Cumplimiento por Línea y Hora",
            font=dict(size=13, color=COLOR_TEXTO_PPAL), x=0,
        ),
        xaxis=dict(**PLOTLY_LAYOUT["xaxis"], title=""),
        yaxis=dict(
            gridcolor=COLOR_BORDE, linecolor=COLOR_BORDE,
            title="", autorange="reversed",
        ),
        height=280,
    )
    fig.update_layout(**layout)
    return fig


def gauge_cumplimiento(valor: float, titulo: str) -> go.Figure:
    """Gauge (velocímetro) para mostrar el KPI de cumplimiento global."""
    color_aguja = color_kpi(valor)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=valor * 100,
        number=dict(suffix="%", font=dict(
            family="IBM Plex Mono", size=28, color=COLOR_TEXTO_PPAL)),
        delta=dict(
            reference=90,
            increasing=dict(color=COLOR_ACENTO_VERDE),
            decreasing=dict(color=COLOR_ACENTO_ROJO),
            font=dict(size=13),
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100], tickwidth=1,
                tickfont=dict(size=10, color=COLOR_TEXTO_SEC),
                tickcolor=COLOR_BORDE,
            ),
            bar=dict(color=color_aguja, thickness=0.25),
            bgcolor=COLOR_SUPERFICIE,
            borderwidth=1,
            bordercolor=COLOR_BORDE,
            steps=[
                dict(range=[0, 75],   color="rgba(248,81,73,0.15)"),
                dict(range=[75, 90],  color="rgba(210,153,34,0.15)"),
                dict(range=[90, 100], color="rgba(63,185,80,0.15)"),
            ],
            threshold=dict(
                line=dict(color=COLOR_ACENTO_AMBAR, width=2),
                thickness=0.7, value=90,
            ),
        ),
        title=dict(
            text=titulo,
            font=dict(size=11, family="IBM Plex Mono", color=COLOR_TEXTO_SEC),
        ),
    ))
    layout = PLOTLY_LAYOUT.copy()
    layout.update(height=220, margin=dict(l=20, r=20, t=40, b=10))
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  BARRA LATERAL
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar(datos: dict) -> dict:
    """
    Renderiza la barra lateral con todos los filtros.
    Devuelve un dict con los valores seleccionados por el usuario.
    """
    with st.sidebar:
        # --- NUEVO BLOQUE DEL LOGO ---
        # --- 1. ESTILO CSS PARA ELIMINAR ESPACIOS GLOBALES ARRIBA ---
        st.markdown("""
            <style>
                /* Quita el espacio en blanco superior de la barra lateral */
                [data-testid="stSidebarUserContent"] {
                    padding-top: 20px !important;
                }
                /* Reduce el espacio entre elementos de la barra lateral */
                [data-testid="stSidebar"] .stVerticalBlock {
                    gap: 0rem !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # --- 2. BLOQUE DEL LOGO CENTRADO ---
        col_izq, col_centro, col_der = st.columns([1, 2, 1])
        with col_centro:
            try:
                # Bajamos un poco el ancho a 100 para que sea más sutil si el espacio es poco
                st.image("Subte_logo.png", width=100)
            except Exception:
                st.markdown("<h4 style='color: white; text-align: center; margin:0;'>Subte BA</h4>", unsafe_allow_html=True)

        # --- 3. TEXTO CON MÁRGENES MÍNIMOS ---
        st.markdown("""
        <div style='margin-top: -10px; padding: 0px 0 10px 0; text-align: center;'>
            <div style='font-size: 0.70rem; color: #8B949E;
                        font-family: IBM Plex Mono; letter-spacing:0.08em; line-height: 1;'>
                TABLERO OPERATIVO
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---") # Una línea divisoria fina para separar de los filtros

        # ── Selector de Vista ──
        vista = st.radio(
            "VISTA",
            options=["Diario / Tiempo Real", "Semanal", "Mensual", "Detalle de Frecuencias"],
            index=0,
        )

        st.markdown("---")

        # ── Filtro de Línea ──
        todas_lineas = sorted(COLORES_LINEAS.keys())
        
        if vista == "Detalle de Frecuencias":
            # Para la tira de frecuencias, forzamos a que elija solo UNA línea a la vez
            linea_sel = st.selectbox("LÍNEA", options=todas_lineas, index=0)
            lineas_sel = [linea_sel]  # Lo metemos en una lista para no romper el resto del código
        else:
            # Selección múltiple clásica para los resúmenes Diario/Semanal/Mensual
            lineas_sel = st.multiselect(
                "LÍNEA",
                options=todas_lineas,
                default=todas_lineas,
                placeholder="Todas las líneas",
            )
            if not lineas_sel:
                lineas_sel = todas_lineas

        # ── Filtro de Sentido ──
        if vista == "Detalle de Frecuencias":
            # Quitamos "Ambos" para no cruzar trenes de ida y vuelta en la misma línea del gráfico
            sentido_opt = ["Asc", "Desc"]
        else:
            sentido_opt = ["Ambos", "Asc", "Desc"]
            
        sentido_sel = st.selectbox("SENTIDO", options=sentido_opt, index=0)

        # ── Filtros según la vista seleccionada ──
        tipo_dia_sel = None
        fecha_sel    = None
        semana_sel   = None
        mes_sel      = None

        if vista == "Diario / Tiempo Real" or vista == "Detalle de Frecuencias":
            df_d   = datos["diario"]
            fechas = sorted(df_d["fecha"].unique(), reverse=True)
            fecha_sel = st.selectbox(
                "FECHA",
                options=fechas,
                format_func=lambda f: f.strftime("%d/%m/%Y"),
            )

        elif vista == "Semanal":
            df_s   = datos["semanal"]
            tipos_dia_d  = ["Habil", "Sabado", "Domingo"]
            tipo_dia_sel = st.multiselect(
                "TIPO DE DÍA", options=tipos_dia_d, default=["Habil"],
            )
            if not tipo_dia_sel:
                tipo_dia_sel = tipos_dia_d

            semanas_disp = sorted(df_s["año_semana"].unique(), reverse=True)
            semana_sel   = st.multiselect(
                "SEMANA(S)",
                options=semanas_disp,
                default=semanas_disp[:4],
                placeholder="Últimas semanas",
            )
            if not semana_sel:
                semana_sel = semanas_disp[:4]

        elif vista == "Mensual":
            df_m   = datos["mensual"]
            tipos_dia_d  = ["Habil", "Sabado", "Domingo"]
            tipo_dia_sel = st.multiselect(
                "TIPO DE DÍA", options=tipos_dia_d, default=["Habil"],
            )
            if not tipo_dia_sel:
                tipo_dia_sel = tipos_dia_d

            meses_disp = sorted(df_m["año_mes"].unique(), reverse=True)
            mes_sel    = st.multiselect(
                "MES(ES)",
                options=meses_disp,
                default=meses_disp,
                placeholder="Todos los meses",
            )
            if not mes_sel:
                mes_sel = meses_disp

        st.markdown("---")

        # ── Nota de datos mock ──
        st.markdown(f"""
        <div style='font-size: 0.70rem; color: {COLOR_TEXTO_SEC};
                    font-family: IBM Plex Mono; line-height:1.6;'>
            Datos reales<br>
            Conectado a la base de datos<br>
        </div>
        """, unsafe_allow_html=True)

    return {
        "vista":        vista,
        "lineas":       lineas_sel,
        "sentido":      sentido_sel,
        "tipo_dia":     tipo_dia_sel,
        "fecha":        fecha_sel,
        "semana":       semana_sel,
        "mes":          mes_sel,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  FILTRADO DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def aplicar_filtros(datos: dict, filtros: dict) -> pd.DataFrame:
    """
    Aplica los filtros de la barra lateral al DataFrame correspondiente
    a la vista seleccionada y devuelve el subconjunto filtrado.
    """
    vista = filtros["vista"]

    if vista == "Diario / Tiempo Real":
        df = datos["diario"].copy()
        if filtros["fecha"]:
            df = df[df["fecha"] == filtros["fecha"]]

    elif vista == "Semanal":
        df = datos["semanal"].copy()
        if filtros["semana"]:
            df = df[df["año_semana"].isin(filtros["semana"])]
        if filtros["tipo_dia"]:
            df = df[df["tipo_dia"].isin(filtros["tipo_dia"])]

    else:  # Mensual
        df = datos["mensual"].copy()
        if filtros["mes"]:
            df = df[df["año_mes"].isin(filtros["mes"])]
        if filtros["tipo_dia"]:
            df = df[df["tipo_dia"].isin(filtros["tipo_dia"])]

    # Filtros comunes
    df = df[df["linea"].isin(filtros["lineas"])]
    if filtros["sentido"] != "Ambos":
        df = df[df["sentido"] == filtros["sentido"]]

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  PANEL PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def render_encabezado(filtros: dict):
    """Encabezado del tablero con título y estado."""
    hoy_str = date.today().strftime("%d de %B de %Y")
    vista   = filtros["vista"]
    lineas_str = ", ".join([f"Línea {l}" for l in filtros["lineas"]]) \
                 if len(filtros["lineas"]) < 5 else "Todas las líneas"

    st.markdown(f"""
    <div class="header-container">
        <div class="status-dot"></div>
        <div>
            <div class="header-title">Tablero Operativo · {vista}</div>
            <div class="header-subtitle">
                {hoy_str} &nbsp;·&nbsp; {lineas_str} &nbsp;·&nbsp;
                Sentido: {filtros['sentido']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_kpis(df: pd.DataFrame):
    """Renderiza las 4 tarjetas KPI del panel superior."""
    if df.empty:
        st.warning("Sin datos para los filtros seleccionados.")
        return

    total_prog  = df["despachos_programados"].sum()
    total_efec  = df["despachos_efectuados"].sum()
    cumpl_gral  = total_efec / total_prog if total_prog > 0 else 0
    reg_gral    = df["indice_regularidad"].mean()
    ie_prom     = df["intervalo_medio_e_sec"].mean()
    ip_prom     = df["intervalo_promedio_programado"].mean()

    col1, col2, col3, col4 = st.columns(4, gap="small")

    with col1:
        render_kpi_card(
            label="Despachos Totales",
            value=f"{total_efec:,}",
            sub=f"de {total_prog:,} programados",
            delta=f"{cumpl_gral*100:.1f}% de cumplimiento",
            delta_pos=(cumpl_gral >= 0.90),
            accent=color_kpi(cumpl_gral),
        )

    with col2:
        render_kpi_card(
            label="Cumplimiento General",
            value=f"{cumpl_gral*100:.1f}%",
            sub=f"Meta: 90%",
            delta=f"{'▲' if cumpl_gral >= 0.90 else '▼'} {'En meta' if cumpl_gral >= 0.90 else 'Bajo meta'}",
            delta_pos=(cumpl_gral >= 0.90),
            accent=color_kpi(cumpl_gral),
        )

    with col3:
        render_kpi_card(
            label="Índice de Regularidad",
            value=f"{reg_gral*100:.1f}%",
            sub="Estabilidad de intervalos",
            delta=f"{'▲' if reg_gral >= 0.90 else '▼'} {'Estable' if reg_gral >= 0.90 else 'Irregular'}",
            delta_pos=(reg_gral >= 0.90),
            accent=color_kpi(reg_gral),
        )

    with col4:
        diferencia_pct = ((ie_prom - ip_prom) / ip_prom * 100) if ip_prom > 0 else 0
        render_kpi_card(
            label="Intervalo Medio",
            value=seg_a_minutos_segundos(ie_prom),
            sub=f"Programado: {seg_a_minutos_segundos(ip_prom)}",
            delta=f"Desvío: {diferencia_pct:+.1f}%",
            delta_pos=(diferencia_pct <= 5),
            accent=color_kpi(1 - abs(diferencia_pct) / 100, umbral_ok=0.95),
        )


def render_graficos_principales(df: pd.DataFrame, filtros: dict):
    """Renderiza los 3 gráficos principales de la sección central."""
    if df.empty:
        return

    vista = filtros["vista"]

    # Determinar el eje X de las series de tiempo según la vista
    if vista == "Diario / Tiempo Real":
        eje_x   = "hora_solo"
        lbl_x   = "hora del día"
    elif vista == "Semanal":
        eje_x   = "año_semana"
        lbl_x   = "semana ISO"
    else:
        eje_x   = "año_mes"
        lbl_x   = "mes"

    st.markdown('<div class="seccion-titulo">Serie Temporal · Análisis de Frecuencia</div>',
                unsafe_allow_html=True)

    col_izq, col_der = st.columns([1, 1], gap="small")

    with col_izq:
        fig_int = grafico_intervalos(
            df, eje_x,
            f"Intervalo Medio: Efectuado vs Programado por {lbl_x}",
        )
        st.plotly_chart(fig_int, use_container_width=True, config={"displayModeBar": False})

    with col_der:
        fig_desp = grafico_despachos(
            df, eje_x,
            f"Despachos por {lbl_x}",
        )
        st.plotly_chart(fig_desp, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="seccion-titulo">Regularidad del Servicio</div>',
                unsafe_allow_html=True)

    col_reg, col_gauge = st.columns([2, 1], gap="small")

    with col_reg:
        fig_reg = grafico_regularidad(
            df, eje_x,
            f"Evolución del Índice de Regularidad por {lbl_x}",
        )
        st.plotly_chart(fig_reg, use_container_width=True, config={"displayModeBar": False})

    with col_gauge:
        cumpl_val = (df["despachos_efectuados"].sum() /
                     df["despachos_programados"].sum()
                     if df["despachos_programados"].sum() > 0 else 0)
        fig_gauge = gauge_cumplimiento(cumpl_val, "Cumplimiento Global")
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})


def render_heatmap(df: pd.DataFrame):
    """Renderiza el mapa de calor de cumplimiento por línea y hora."""
    if df.empty or "hora_solo" not in df.columns:
        return

    st.markdown('<div class="seccion-titulo">Distribución de Cumplimiento · Detalle por Línea</div>',
                unsafe_allow_html=True)

    fig_hm = grafico_mapa_calor_linea(df)
    st.plotly_chart(fig_hm, use_container_width=True, config={"displayModeBar": False})


def render_tabla_resumen(df: pd.DataFrame, filtros: dict):
    """Tabla de resumen por línea con los KPIs agregados."""
    if df.empty:
        return

    st.markdown('<div class="seccion-titulo">Resumen por Línea</div>',
                unsafe_allow_html=True)

    resumen = (df.groupby("linea", as_index=False)
                 .agg(
                     prog=("despachos_programados",  "sum"),
                     efec=("despachos_efectuados",   "sum"),
                     ie  =("intervalo_medio_e_sec",  "mean"),
                     ip  =("intervalo_promedio_programado", "mean"),
                     reg =("indice_regularidad",     "mean"),
                 ))
    resumen["cumpl"]   = (resumen["efec"] / resumen["prog"]).clip(0, 1)
    resumen["ie_fmt"]  = resumen["ie"].apply(seg_a_minutos_segundos)
    resumen["ip_fmt"]  = resumen["ip"].apply(seg_a_minutos_segundos)

    # DataFrame para mostrar
    tabla = resumen[[
        "linea", "prog", "efec", "cumpl", "reg", "ie_fmt", "ip_fmt"
    ]].rename(columns={
        "linea": "Línea",
        "prog":  "Desp. Prog.",
        "efec":  "Desp. Efec.",
        "cumpl": "Cumplimiento",
        "reg":   "Regularidad",
        "ie_fmt":"Intervalo Efec.",
        "ip_fmt":"Intervalo Prog.",
    })

    tabla["Cumplimiento"] = tabla["Cumplimiento"].map(lambda v: f"{v*100:.1f}%")
    tabla["Regularidad"]  = tabla["Regularidad"].map(lambda v: f"{v*100:.1f}%")
    tabla["Desp. Prog."]  = tabla["Desp. Prog."].map(lambda v: f"{v:,.0f}")
    tabla["Desp. Efec."]  = tabla["Desp. Efec."].map(lambda v: f"{v:,.0f}")

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Línea":           st.column_config.TextColumn(width="small"),
            "Cumplimiento":    st.column_config.TextColumn(width="medium"),
            "Regularidad":     st.column_config.TextColumn(width="medium"),
            "Intervalo Efec.": st.column_config.TextColumn(width="medium"),
            "Intervalo Prog.": st.column_config.TextColumn(width="medium"),
        },
    )

# -------------------------------------------------------------------------
# NUEVA FUNCIÓN: RENDERIZAR TIRAS DE INTERVALOS (FRECUENCIAS)
# -------------------------------------------------------------------------
def render_detalle_frecuencia(df, filtros):
    st.markdown(f'<div class="seccion-titulo">Tira de Intervalos Individuales - {filtros["linea"]} ({filtros["sentido"]})</div>', unsafe_allow_html=True)
    
    if df.empty:
        st.info("No hay datos de despachos para los filtros y fecha seleccionados.")
        return

    # Ordenar la tabla cronológicamente
    df = df.sort_values(by=["hora_solo", "turno_en_la_hora"])
    
    # ── 1. Mini KPIs de la Tira ──
    col1, col2, col3, col4 = st.columns(4)
    
    despachos_prog = df["hora_programada"].count()
    despachos_reales = df["hora_real"].count()
    
    int_prom_prog = df["intervalo_segundos_franja_p"].mean() if "intervalo_segundos_franja_p" in df else np.nan
    int_prom_real = df["intervalo_segundos_franja_e"].mean() if "intervalo_segundos_franja_e" in df else np.nan
    
    col1.metric("Despachos Programados", f"{despachos_prog}")
    col2.metric("Despachos Reales", f"{despachos_reales}")
    
    if pd.notna(int_prom_prog) and int_prom_prog > 0:
        m, s = divmod(int_prom_prog, 60)
        col3.metric("Intervalo Prom. Programado", f"{int(m):02d}:{int(s):02d}")
    else:
        col3.metric("Intervalo Prom. Programado", "-")

    if pd.notna(int_prom_real) and int_prom_real > 0:
        m, s = divmod(int_prom_real, 60)
        delta = int_prom_real - int_prom_prog if pd.notna(int_prom_prog) else 0
        delta_str = f"{int(delta)} seg" if delta != 0 else None
        col4.metric("Intervalo Prom. Real", f"{int(m):02d}:{int(s):02d}", delta_str, delta_color="inverse")
    else:
        col4.metric("Intervalo Prom. Real", "-")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 2. Gráfico de Tira de Intervalos (Fluctuación) ──
    fig = go.Figure()
    
    if "intervalo_segundos_franja_p" in df and "hora_programada" in df:
        df_prog = df.dropna(subset=["hora_programada", "intervalo_segundos_franja_p"]).sort_values("hora_programada")
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df_prog["hora_programada"].astype(str), format='%H:%M:%S', errors='coerce'),
            y=df_prog["intervalo_segundos_franja_p"] / 60,
            mode='lines+markers', name='Prog. (Minutos)',
            line=dict(color='#A0AAB2', width=2, dash='dash'),
            marker=dict(size=6, symbol='circle'),
            hovertemplate="Hora Prog: %{x|%H:%M:%S}<br>Intervalo: %{y:.1f} min<extra></extra>"
        ))
        
    if "intervalo_segundos_franja_e" in df and "hora_real" in df:
        df_real = df.dropna(subset=["hora_real", "intervalo_segundos_franja_e"]).sort_values("hora_real")
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df_real["hora_real"].astype(str), format='%H:%M:%S', errors='coerce'),
            y=df_real["intervalo_segundos_franja_e"] / 60,
            mode='lines+markers', name='Real (Minutos)',
            line=dict(color='#0078D7', width=3),
            marker=dict(size=8, symbol='diamond'),
            hovertemplate="Hora Real: %{x|%H:%M:%S}<br>Intervalo: %{y:.1f} min<extra></extra>"
        ))
        
    fig.update_layout(
        title="Evolución del Intervalo entre Trenes (Tira de Despachos)",
        xaxis_title="Hora de Despacho", 
        yaxis_title="Intervalo (Minutos)",
        xaxis=dict(tickformat="%H:%M"), 
        template="plotly_white", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ── 3. Tabla de Datos Crudos ──
    st.markdown("### 📋 Detalle de Despachos")
    columnas_mostrar = {
        "linea":"linea","sentido": "Sentido","hora_solo": "Hora", "turno_en_la_hora": "Turno",
        "formacion_programada": "Chapa Prog.", "hora_programada": "Hora Prog.",
        "intervalo_franja_p": "Intervalo Prog.", "formacion_real": "Chapa Real",
        "hora_real": "Hora Real", "intervalo_franja_e": "Intervalo Real",
        "promedio_bloque": "Prom. del Bloque"
    }
    
    cols_existentes = [c for c in columnas_mostrar.keys() if c in df.columns]
    df_tabla = df[cols_existentes].copy()
    df_tabla.rename(columns=columnas_mostrar, inplace=True)
    
    # Funciones de formateo de tiempo
    def formatear_segundos(segs):
        if pd.isna(segs): return ""
        s = int(segs)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"

    def formatear_intervalo(val):
        if pd.isna(val): return ""
        if isinstance(val, pd.Timedelta):
            s = int(val.total_seconds())
            return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
        return str(val)[-8:] 

    if "Prom. del Bloque" in df_tabla.columns:
        df_tabla["Prom. del Bloque"] = df_tabla["Prom. del Bloque"].apply(formatear_segundos)

    if "Intervalo Prog." in df_tabla.columns:
        df_tabla["Intervalo Prog."] = df_tabla["Intervalo Prog."].apply(formatear_intervalo)

    if "Intervalo Real" in df_tabla.columns:
        df_tabla["Intervalo Real"] = df_tabla["Intervalo Real"].apply(formatear_intervalo)
    
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PUNTO DE ENTRADA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Función principal que orquesta el renderizado del dashboard."""

    # 1. Cargar datos
    datos = get_postgres_data()

    # 2. Renderizar barra lateral y obtener filtros
    filtros = render_sidebar(datos)

    # 3. Lógica de renderizado principal (El IF/ELSE)
    if filtros["vista"] == "Detalle de Frecuencias":
        
        # Obtenemos la tabla de frecuencias
        df_freq = datos.get("frecuencia", pd.DataFrame()).copy()
        
        if not df_freq.empty:
            # Para la tira de intervalos, es mejor ver UNA sola línea a la vez.
            # Tomamos la primera que el usuario haya seleccionado.
            linea_seleccionada = filtros["lineas"][0] if filtros["lineas"] else "A"
            df_freq = df_freq[df_freq["linea"] == linea_seleccionada]
            
            if filtros["sentido"] != "Ambos":
                df_freq = df_freq[df_freq["sentido"] == filtros["sentido"]]
                
            # Si en el menú lateral hay una fecha seleccionada, filtramos la tabla
            if filtros.get("fecha"):
                df_freq = df_freq[df_freq["fecha"] == filtros["fecha"]]

        # Creamos un filtro modificado solo para pasarle a la función gráfica el nombre de la línea
        filtros_detalle = filtros.copy()
        filtros_detalle["linea"] = linea_seleccionada if filtros["lineas"] else "A"
        
        # Dibujamos la nueva vista
        render_detalle_frecuencia(df_freq, filtros_detalle)

    else:
        # --- RENDERIZADO CLÁSICO (Diario / Semanal / Mensual) ---
        
        # Aplicamos los filtros globales a las vistas clásicas
        df_filtrado = aplicar_filtros(datos, filtros)
        
        render_encabezado(filtros)

        st.markdown('<div class="seccion-titulo">Indicadores Clave de Desempeño (KPI)</div>', unsafe_allow_html=True)
        render_kpis(df_filtrado)

        st.markdown("<br>", unsafe_allow_html=True)
        render_graficos_principales(df_filtrado, filtros)

        st.markdown("<br>", unsafe_allow_html=True)
        render_heatmap(df_filtrado)

        st.markdown("<br>", unsafe_allow_html=True)
        render_tabla_resumen(df_filtrado, filtros)

    # ── Pie de página ──
    st.markdown(f"""
    <div style='text-align:center; padding: 32px 0 8px 0;
                font-family: IBM Plex Mono, monospace;
                font-size: 0.70rem; color: #8B949E;'>
        Subte Buenos Aires · Tablero Operativo v1.0 &nbsp;|&nbsp;
        Datos: {date.today().strftime('%d/%m/%Y')}
    </div>
    """, unsafe_allow_html=True)
    
if __name__ == "__main__":
    main()
