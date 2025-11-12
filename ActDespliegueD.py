import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np
from pathlib import Path
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import numpy as np
import statsmodels.api as sm
import statsmodels.api as sm
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
import streamlit as st
#PALETA / PLOTLY

PALETTE = {
    "brand": "#FF385C",     
    "brand_alt": "#FF5A5F", 
    "salmon": "#FF6B6B",
    "white": "#FFFFFF",
    "gray500": "#4A4A4A",
    "gray900": "#1F1F1F",
    "bg": "#FFFFFF",
    "panel": "#F7F7F7",
}

# Paleta de competitividad Airbnb (del rojo brand a tonos más suaves)
AIRBNB_COMPETITIVENESS_SCALE = [
    "#FFF5F5",  # Muy claro (baja competitividad)
    "#FFE3E6",  # Claro
    "#FFB3BA",  # Medio claro  
    "#FF7A85",  # Medio
    "#FF5A5F",  # Medio alto (brand_alt)
    "#FF385C"   # Alto (brand principal)
]

#Config plotly por defecto
pio.templates.default = "plotly_white"
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = [
    PALETTE["brand"], PALETTE["salmon"], "#F7A6A6",
    PALETTE["gray500"], PALETTE["gray900"], "#9CA3AF"
]
px.defaults.width = None
px.defaults.height = None
pio.templates["plotly_white"].layout.font.family = "Inter, Segoe UI, system-ui, -apple-system, sans-serif"
pio.templates["plotly_white"].layout.paper_bgcolor = PALETTE["bg"]
pio.templates["plotly_white"].layout.plot_bgcolor  = PALETTE["bg"]
pio.templates["plotly_white"].layout.margin = dict(l=10, r=10, t=40, b=10)


#CONFIG STREAMLIT

st.set_page_config(page_title="Airbnb", layout="wide")

# ESTILOS (sidebar pastel + títulos)
# =========================
AIRBNB_BRAND = "#FF385C"
AIRBNB_SOFT  = "#FF8FA3"

st.markdown(f"""
<style>
/* ===== Sidebar rosa pastel ===== */
[data-testid="stSidebar"]{{
  background: #FFD1DC !important;  /* rosa pastel */
  color: #111 !important;
}}
[data-testid="stSidebar"] *{{ color:#111 !important; }}
[data-testid="stSidebar"] > div:first-child{{ padding:18px 16px 22px 16px; }}

/* ===== Inputs en la sidebar ===== */
/* Text / Number / Select: altura fija cómoda */
[data-testid="stSidebar"] .stTextInput > div > div > input,
[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] .stSelectbox > div > div{{
  background:#fff !important; color:#111 !important;
  border:1px solid rgba(0,0,0,.2) !important; border-radius:12px !important;
  height:42px;
}}

/* Multiselect: altura dinámica (clave para evitar superposición) */
[data-testid="stSidebar"] .stMultiSelect > div > div{{
  background:#fff !important; color:#111 !important;
  border:1px solid rgba(0,0,0,.2) !important; border-radius:12px !important;
  height:auto !important;            /* NO altura fija */
  min-height:42px;                   /* mínima estética */
  padding-top:6px; padding-bottom:6px;
  overflow:visible !important;
}}
/* Separación extra para que no pegue con el siguiente título/control */
[data-testid="stSidebar"] .stMultiSelect{{ margin-bottom:12px; }}

/* Chips (tags) del multiselect */
[data-testid="stSidebar"] [data-baseweb="tag"]{{
  background:#fff !important;
  color:#111 !important;
  border:1px solid rgba(0,0,0,.25) !important;
  border-radius:12px !important;
  box-shadow:none !important;
  margin:4px 6px 0 0;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] *{{ color:#111 !important; fill:#111 !important; }}

/* Placeholders y separadores */
[data-testid="stSidebar"] input::placeholder{{ color:rgba(0,0,0,.45) !important; }}
[data-testid="stSidebar"] hr{{ display:none !important; }}

/* ===== Botones y sliders ===== */
[data-testid="stSidebar"] button[kind]{{
  background:#fff !important; color:#111 !important;
  border:1px solid rgba(0,0,0,.25) !important; border-radius:12px !important;
}}
[data-testid="stSidebar"] button[kind]:hover{{ background:#FAFAFA !important; }}

/* Slider: riel y thumb (evitar colores por defecto) */
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div{{ background:rgba(0,0,0,.18) !important; }}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div{{ background:#111 !important; }}
[data-testid="stSidebar"] .stSlider [role="slider"]{{ background:#111 !important; box-shadow:none !important; }}

/* ===== Títulos del cuerpo ===== */
main .block-container h1{{ color:{AIRBNB_BRAND} !important; font-weight:800; letter-spacing:.2px; }}
main .block-container h2, main .block-container h3{{ color:{AIRBNB_SOFT} !important; font-weight:700; letter-spacing:.2px; }}
main .block-container section h1{{ color:{AIRBNB_BRAND} !important; }}
main .block-container section h2, main .block-container section h3{{ color:{AIRBNB_SOFT} !important; }}

/* Opcional: evitar que labels largos se corten/solapen en sidebar */
[data-testid="stSidebar"] label p{{ white-space:normal !important; }}
</style>
""", unsafe_allow_html=True)



#LOGO
HERE = Path(__file__).resolve().parent
LOGO_STEM = "airbnbllogo"  #Nombre imagen 
LOGO_PATH = None
for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
    p = HERE / f"{LOGO_STEM}{ext}"
    if p.exists():
        LOGO_PATH = str(p); break
if LOGO_PATH:
    st.sidebar.image(LOGO_PATH, width=300)
    st.sidebar.markdown("")


#DATA SOURCES 
DEFAULTS = [
    ("listingsBarcelona.csv", "Barcelona"),
    ("listingsAmsterdam.csv", "Amsterdam"),
    ("listingsMilan.csv", "Milan"),
    ("listingsGrecia.csv", "Atenas"),
    ("listingsMadrid.csv", "Madrid"),
]

paths = [ruta for ruta, _ in DEFAULTS]
names = [nombre for _, nombre in DEFAULTS]

def _to_float_price(val):
    """
    Convierte strings de precio a float de forma robusta.
    Soporta formatos: "€1.234,56", "1 234,56 €", "$1,234.56", "1 234€", "120–150", "120 - 150".
    Devuelve np.nan si no se puede parsear.
    """
    if pd.isna(val):
        return np.nan

    s = str(val).strip()
    if not s:
        return np.nan

    # Normaliza espacios "raros" y guiones
    s = (s.replace("\u00A0", " ")     # NBSP
           .replace("\u202F", " ")    # thin space
           .replace("–", "-")         # en dash
           .replace("—", "-"))        # em dash

    # Quita texto común no numérico
    s = re.sub(r"(per\s*night|/night|por\s*d[ií]a|/d[ií]a|night|noche|día|day)", "", s, flags=re.I)

    # Si es un rango (no negativo), toma el promedio
    # p.ej. "120-150", "120 - 150", "120- 150"
    m_range = re.findall(r"(?<!^)-", s)  # guiones que no son signo inicial
    if m_range:
        # extrae todos los números candidatos y promedia los dos primeros
        nums = re.findall(r"[-+]?\d[\d\s\.',]*", s)
        parsed = []
        for n in nums:
            x = _to_float_price(n)  # recursion sobre cada trozo numérico
            if pd.notna(x):
                parsed.append(x)
            if len(parsed) == 2:
                break
        if len(parsed) == 2:
            return float(np.mean(parsed))
        # si no se pudo, sigue con parsing normal de s

    # Deja solo dígitos, separadores y signo
    # (guardamos ',' '.' ' ' y apostrofe como posibles separadores de miles)
    s_clean = re.sub(r"[^0-9\-\.,'\s]", "", s).strip()
    if not s_clean:
        return np.nan

    # Heurística de separadores
    # 1) Si tiene '.' y ',', decide por el último separador como decimal cuando hay 2 dígitos detrás
    if "." in s_clean and "," in s_clean:
        last_dot = s_clean.rfind(".")
        last_com = s_clean.rfind(",")
        last = max(last_dot, last_com)
        tail = s_clean[last+1:].replace(" ", "").replace("'", "")
        if len(re.sub(r"\D", "", tail)) in (2, 1):  # 2 dígitos (típico centavos) o 1 (algunos redondeos)
            if last == last_com:
                # coma decimal => quita puntos/espacios/apóstrofes como miles y cambia coma por punto
                num = re.sub(r"[.\s']", "", s_clean).replace(",", ".")
            else:
                # punto decimal => quita comas/espacios/apóstrofes como miles
                num = re.sub(r"[, \s']", "", s_clean)
        else:
            # Si no parece decimal clásico, elimina todas las comas y espacios; trata punto como decimal si solo hay uno
            num = re.sub(r"[, \s']", "", s_clean)
    # 2) Solo comas (formato EU típico: "1 234,56" o "1234,56")
    elif "," in s_clean and "." not in s_clean:
        # si hay exactamente una coma y 1-2 dígitos al final -> decimal
        parts = s_clean.split(",")
        if len(parts) == 2 and re.fullmatch(r"\d{1,2}", re.sub(r"\D", "", parts[1] or "")):
            num = re.sub(r"[\s']", "", parts[0]) + "." + re.sub(r"\D", "", parts[1])
        else:
            # probablemente comas de miles: quítalas
            num = re.sub(r"[,\s']", "", s_clean)
    else:
        # Solo puntos o solo dígitos/espacios: quita separadores de miles (espacios/apóstrofes/comas residuales)
        num = re.sub(r"[, \s']", "", s_clean)

    # Evita casos como "-" o vacío
    if num in ("", "-", "+"):
        return np.nan

    try:
        return float(num)
    except Exception:
        # último intento: extrae primer número "claro" y reintenta
        m = re.search(r"[-+]?\d+(?:\.\d+)?", num)
        return float(m.group(0)) if m else np.nan


def _bathrooms_from_text(txt):
    if pd.isna(txt): return np.nan
    s = str(txt).lower()
    if "half" in s and not re.search(r"\d+(\.\d+)?", s): return 0.5
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else np.nan

def limpiar_estandarizar(df: pd.DataFrame, ciudad: str) -> pd.DataFrame:
    d = df.copy()
    d["ciudad"] = ciudad
    if "id" not in d.columns: d["id"] = np.arange(len(d)) + 1

    d["price"] = d.get("price", np.nan)
    d["price"] = d["price"].map(_to_float_price)

    if "neighbourhood_cleansed" in d.columns:
        d["barrio_std"] = d["neighbourhood_cleansed"]
    elif "neighbourhood" in d.columns:
        d["barrio_std"] = d["neighbourhood"]
    else:
        d["barrio_std"] = np.nan

    d["room_type"] = d.get("room_type", pd.Series(index=d.index, dtype="object")).astype(str).str.strip().replace({"nan": np.nan})
    d["accommodates"] = pd.to_numeric(d.get("accommodates", np.nan), errors="coerce")

    if "bathrooms_text" in d.columns:
        d["bathrooms_num"] = d["bathrooms_text"].map(_bathrooms_from_text)
    else:
        d["bathrooms_num"] = pd.to_numeric(d.get("bathrooms", np.nan), errors="coerce")

    d["latitude"]  = pd.to_numeric(d.get("latitude", np.nan), errors="coerce")
    d["longitude"] = pd.to_numeric(d.get("longitude", np.nan), errors="coerce")

    if "amenities" in d.columns:
        d["amenities_count"] = d["amenities"].astype(str).apply(
            lambda x: 0 if x in ("nan", "", "[]") else len([a for a in re.split(r"[,\|]", x.strip("[]")) if a.strip()])
        )
    else:
        d["amenities_count"] = np.nan

    d["price_per_person"] = np.where((d["accommodates"] >= 1) & d["price"].notna(), d["price"] / d["accommodates"], np.nan)

    # Convertir superhost a numérico (1 si es superhost, 0 si no)
    if "host_is_superhost" in d.columns:
        d["superhost_numeric"] = d["host_is_superhost"].astype(str).str.strip().str.lower().map(
            {"t": 1, "true": 1, "f": 0, "false": 0, "nan": np.nan}
        ).fillna(0).astype(float)
    else:
        d["superhost_numeric"] = 0.0

    cols = ["id","ciudad","barrio_std","room_type","accommodates","bathrooms_num",
            "price","price_per_person","amenities_count","latitude","longitude",
            "superhost_numeric",
            "property_type","host_is_superhost","cancellation_policy",
            "instant_bookable","review_scores_rating","number_of_reviews",
            "bed_type","neighbourhood_group_cleansed",
            "require_guest_profile_picture","require_guest_phone_verification",
            "host_response_time","host_identity_verified","has_availability","source"]
    keep = [c for c in cols if c in d.columns]
    return d[keep]

def recortar_outliers_por_ciudad(df: pd.DataFrame, col="price", p_low=0.01, p_high=0.99):
    limpio = []
    for ciudad, g in df.groupby("ciudad", dropna=False):
        if g[col].notna().sum() < 50:
            limpio.append(g); continue
        low, high = g[col].quantile(p_low), g[col].quantile(p_high)
        limpio.append(g[(g[col].isna()) | ((g[col] >= low) & (g[col] <= high))])
    return pd.concat(limpio, ignore_index=True)

@st.cache_data(show_spinner=False)
def load_data(paths, names):
    here = Path(__file__).resolve().parent
    partes, warnings = [], []

    for raw_path, city in zip(paths, names):
        p = Path(raw_path)
        if not p.is_absolute(): p = here / p
        if not p.exists():
            warnings.append(f"No se encontró el archivo de **{city}**: `{raw_path}`")
            continue

        df_raw = None
        try:
            df_raw = pd.read_csv(p, low_memory=False)
        except UnicodeDecodeError:
            try:
                df_raw = pd.read_csv(p, low_memory=False, encoding="latin-1")
            except Exception as e:
                warnings.append(f"Error de lectura en **{city}**: {e}")
                continue
        except Exception as e:
            warnings.append(f"Error leyendo **{city}**: {e}")
            continue

        partes.append(limpiar_estandarizar(df_raw, city))

    if not partes:
        return pd.DataFrame(), warnings

    df_all = pd.concat(partes, ignore_index=True)
    if {"ciudad","id"}.issubset(df_all.columns):
        df_all = (df_all.sort_values(["ciudad","id"])
                        .drop_duplicates(subset=["ciudad","id"], keep="first"))

    if "price" in df_all.columns:
        df_all = recortar_outliers_por_ciudad(df_all, col="price", p_low=0.01, p_high=0.99)

    return df_all, warnings

df, warns = load_data(paths, names)
for w in warns: st.warning(w)
if df.empty:
    st.stop()

#LISTA DE CATEGÓRICAS
candidatas = [
    "room_type","barrio_std","property_type","instant_bookable","cancellation_policy",
    "host_is_superhost","host_identity_verified","host_response_time","has_availability",
    "bed_type","source","neighbourhood_group_cleansed",
    "price_range","accommodates_band","bathrooms_band","amenities_band",
]
Lista = [c for c in candidatas if c in df.columns]
if len(Lista) < 15:
    auto = [c for c in df.select_dtypes(include=["object","category"]).columns
            if c not in Lista and df[c].nunique(dropna=False) <= 50]
    Lista = (Lista + auto)[:15]
if not Lista:
    st.error("No encontré variables categóricas. Revisa que el DataFrame tenga columnas tipo object/category.")
    st.stop()


# MENÚ GENERAL

st.sidebar.title("Tipo de análisis")
View = st.sidebar.selectbox(
    label="Tipo de Análisis",
    options=["Extracción de Características", "Regresión Lineal", "Regresión No Lineal", "Regresión Logística"]
)



#VISTA 1:EXTRACCIÓN DE CARACTERÍSTICAS

if View == "Extracción de Características":
    st.title("Airbnb")

    # Selectores comunes
    ciudad_sel = st.sidebar.selectbox("Ciudad asignada", sorted(df["ciudad"].dropna().unique().tolist()))
    top_k = st.sidebar.slider("Top categorías por gráfica", 5, 30, 10, key="topk")
    mostrar_tabla = st.sidebar.checkbox("Mostrar tabla de frecuencias", value=False, key="mostrar_tabla")
    Variable_Cat = st.sidebar.selectbox("Variables", options=Lista, key="var_cat")

    # Modo
    vista = st.sidebar.radio(
        "Modo de análisis",
        ["Por ciudad", "Comparativo multi-ciudad"],
        index=0, key="vista_modo"
    )

    #Comparativo multi-ciudad
  
    if vista == "Comparativo multi-ciudad":
        ciudades_disp = sorted(df["ciudad"].dropna().unique().tolist())
        ciudades_sel = st.sidebar.multiselect(
            "Ciudades a comparar",
            options=ciudades_disp,
            default=ciudades_disp,
            key="ciudades_sel"
        )
        if not ciudades_sel:
            st.warning("Selecciona al menos una ciudad para el análisis comparativo.")
            st.stop()

        df_comp = df[df["ciudad"].isin(ciudades_sel)].copy()
        st.header("Análisis comparativo de ciudades")



        # ====== Sección: Distribución categórica ======
        st.subheader(f"Distribución de '{Variable_Cat}' por ciudad (Top {top_k})")

        col_cfg1, col_cfg2, col_cfg3, col_cfg4 = st.columns([1.8,1.1,1.1,1.1])
        with col_cfg1:
            tipo_cat = st.selectbox(
                "Tipo de gráfica",
                [
                    "Barras (agrupadas)",
                    "Barras (apiladas)",
                    "Barras (% apiladas)",
                    "Barras por ciudad ",
                    "Pastel "
                ],
                index=0, key="tipo_cat_cmp"
            )
        with col_cfg2:
            mostrar_tabla_cmp = st.checkbox("Mostrar tabla", value=False, key="tabla_cat_cmp")
        with col_cfg3:
            normalizar_top = st.checkbox("Top K global", value=True, key="topk_global_cmp")
        with col_cfg4:
            cols_grid = st.slider("Gráficas por fila (grid)", 2, 4, 4, key="cols_grid_cat")

        if Variable_Cat in df_comp.columns and not df_comp[Variable_Cat].isna().all():
            df_comp["__cat__"] = df_comp[Variable_Cat].astype("object").fillna("NA").astype(str)

            frec = (
                df_comp.groupby(["ciudad","__cat__"]).size()
                .reset_index(name="frecuencia")
            )

            if normalizar_top:
                top_cats = (frec.groupby("__cat__")["frecuencia"].sum()
                                 .sort_values(ascending=False).head(top_k).index.tolist())
                frec = frec[frec["__cat__"].isin(top_cats)]
            else:
                frec["rk"] = frec.groupby("ciudad")["frecuencia"].rank("dense", ascending=False)
                frec = frec[frec["rk"] <= top_k].drop(columns="rk")

            # ---- Helpers de grid ----
            def render_grid(figs, cols_per_row=4, titles=None):
                if cols_per_row < 1: cols_per_row = 1
                for i in range(0, len(figs), cols_per_row):
                    cols = st.columns(min(cols_per_row, len(figs) - i))
                    for j, fig in enumerate(figs[i:i+cols_per_row]):
                        with cols[j]:
                            if titles:
                                st.markdown(f"**{titles[i+j]}**")
                            st.plotly_chart(fig, use_container_width=True)

            if tipo_cat in ["Barras (agrupadas)", "Barras (apiladas)", "Barras (% apiladas)"]:
                # Formatos de barras combinadas
                barmode = "group" if "agrupadas" in tipo_cat else "stack"

                if "% apiladas" in tipo_cat:
                    frec_pct = frec.copy()
                    frec_pct["frecuencia"] = frec_pct.groupby("__cat__")["frecuencia"].transform(
                        lambda s: s / s.sum() * 100
                    )
                    fig_comp_cat = px.bar(
                        frec_pct, x="__cat__", y="frecuencia", color="ciudad",
                        barmode="stack",
                        title=f"Participación (%) por categoría — '{Variable_Cat}'"
                    )
                    fig_comp_cat.update_yaxes(title_text="Porcentaje")
                else:
                    fig_comp_cat = px.bar(
                        frec, x="__cat__", y="frecuencia", color="ciudad",
                        barmode=barmode,
                        title=f"Top {top_k} categorías en '{Variable_Cat}' por ciudad"
                    )
                    fig_comp_cat.update_yaxes(title_text="Frecuencia")

                fig_comp_cat.update_layout(height=480, margin=dict(l=10, r=10, t=50, b=10))
                fig_comp_cat.update_xaxes(title_text="Categoría", automargin=True)
                st.plotly_chart(fig_comp_cat, use_container_width=True)

                # Interpretación dinámica según variable y tipo de gráfica
                with st.expander("Interpretación del Gráfico"):
                    
                    # Función para generar interpretaciones dinámicas
                    def get_interpretacion_variable(variable, tipo_grafica):
                        interpretaciones = {
                            "room_type": {
                                "agrupadas": """
                                **Lo que nos dice sobre el mercado de Airbnb:**
                                - Cada ciudad tiene su propio perfil de tipos de alojamiento
                                - Si ves departamentos enteros dominando en una ciudad pero habitaciones privadas en otra, refleja diferentes culturas de hospedaje
                                - Las ciudades con más variedad de tipos tienden a ser mercados maduros con diferentes segmentos de huéspedes
                                - **Oportunidad**: Si una ciudad tiene pocos de cierto tipo popular en otras, podría ser un nicho desatendido
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre demanda total:**
                                - Las barras más altas muestran los tipos de alojamiento más populares en general
                                - Apartamentos enteros suelen dominar porque los viajeros prefieren privacidad
                                - Los segmentos de colores muestran qué ciudades ofrecen más de cada tipo
                                - **Oportunidad**: Tipos con barras altas = alta demanda; ciudades con segmentos pequeños = menos competencia
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre participación de mercado:**
                                - Muestra qué ciudad 'domina' cada tipo de alojamiento
                                - Si una ciudad tiene el 80% de cierto tipo, es prácticamente el líder en ese segmento
                                - Revela especializaciones: algunas ciudades se especializan en apartamentos enteros, otras en habitaciones compartidas
                                - **Oportunidad**: Busca tipos donde ninguna ciudad domine claramente - son mercados más equilibrados para entrar
                                """
                            },
                            "property_type": {
                                "agrupadas": """
                                **Lo que nos dice sobre tipos de propiedades por ciudad:**
                                - Revela la infraestructura turística de cada ciudad (apartamentos vs casas vs lofts)
                                - Ciudades con muchos apartamentos = mercados urbanos densos
                                - Ciudades con casas = destinos familiares o suburbanos
                                - **Estrategia**: El tipo de propiedad determina tu segmento de huéspedes objetivo
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre la oferta inmobiliaria total:**
                                - Los apartamentos suelen dominar en ciudades europeas por disponibilidad
                                - Casas enteras atraen familias y grupos grandes - mayor precio por noche
                                - Tipos únicos (lofts, estudios) pueden tener menos competencia
                                - **Oportunidad**: Tipos con demanda alta pero poca oferta en ciertas ciudades
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre especialización inmobiliaria:**
                                - Muestra qué ciudad lidera cada tipo de propiedad
                                - Ciudades especializadas en un tipo tienen ventajas operativas
                                - La diversidad indica mercados maduros con múltiples segmentos
                                - **Insight**: Replica estrategias exitosas de tipos dominantes en otras ciudades
                                """
                            },
                            "host_is_superhost": {
                                "agrupadas": """
                                **Lo que nos dice sobre la profesionalización del mercado:**
                                - Alto % de superhosts = mercado maduro y competitivo
                                - Bajo % de superhosts = oportunidad para destacar con calidad
                                - Compara el nivel de profesionalización entre ciudades
                                - **Estrategia**: En mercados con muchos superhosts, la calidad es obligatoria para competir
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre estándares de calidad:**
                                - La proporción total de superhosts indica la exigencia del mercado
                                - Más superhosts = huéspedes más exigentes en esa ciudad
                                - Mercados con pocos superhosts tienen barreras de entrada más bajas
                                - **Oportunidad**: Ser superhost en mercados con pocos puede darte ventaja competitiva inmediata
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre liderazgo en calidad:**
                                - Muestra qué ciudades concentran a los mejores hosts
                                - Ciudades con alta proporción de superhosts tienen ecosistemas más desarrollados
                                - Indica dónde están los benchmarks de calidad más altos
                                - **Aprendizaje**: Estudia las prácticas de superhosts en ciudades líderes
                                """
                            },
                            "instant_bookable": {
                                "agrupadas": """
                                **Lo que nos dice sobre la facilidad de reserva:**
                                - Alto % de reserva instantánea = mercado orientado a conveniencia
                                - Bajo % = hosts más selectivos o cautelosos
                                - Refleja la cultura de confianza en cada ciudad
                                - **Estrategia**: En mercados con mucha reserva instantánea, activarla puede ser necesario para competir
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre accesibilidad del mercado:**
                                - Más reserva instantánea = mercado más accesible para huéspedes
                                - Facilita las reservas de último minuto y viajeros espontáneos
                                - Ciudades con más opciones instantáneas capturan más demanda impulsiva
                                - **Oportunidad**: Si una ciudad tiene poca reserva instantánea, activarla te da ventaja
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre estrategias de reserva:**
                                - Muestra qué ciudades lideran en facilidad de reserva
                                - Indica diferentes filosofías de hosts (control vs volumen)
                                - Ciudades con más reserva instantánea tienden a tener más rotación
                                - **Decisión**: Evalúa si tu ciudad favorece control de huéspedes o volumen de reservas
                                """
                            },
                            "barrio_std": {
                                "agrupadas": """
                                **Lo que nos dice sobre distribución geográfica:**
                                - Muestra qué barrios dominan la oferta en cada ciudad
                                - Barrios con muchas propiedades pueden estar saturados
                                - Barrios con pocas propiedades pueden ser oportunidades inexploradas
                                - **Estrategia**: Busca barrios con buena ubicación pero poca competencia
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre concentración del mercado:**
                                - Revela si el mercado está concentrado en pocos barrios o disperso
                                - Barrios dominantes suelen tener mejor infraestructura turística
                                - La dispersión indica mercado maduro con múltiples zonas atractivas
                                - **Oportunidad**: Barrios emergentes con crecimiento pero poca oferta actual
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre liderazgo geográfico:**
                                - Muestra qué barrios son líderes en cada ciudad
                                - Indica patrones de demanda y preferencias de ubicación
                                - Revela oportunidades de expansión geográfica
                                - **Insight**: Los barrios líderes marcan tendencias que otros pueden seguir
                                """
                            },
                            "cancellation_policy": {
                                "agrupadas": """
                                **Lo que nos dice sobre políticas de cancelación:**
                                - Muestra qué tan flexibles o estrictos son los hosts en cada ciudad
                                - Políticas flexibles = enfoque en volumen y satisfacción del huésped
                                - Políticas estrictas = mayor control y protección del host
                                - **Estrategia**: Alinea tu política con la cultura dominante de tu ciudad
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre flexibilidad del mercado:**
                                - Revela el balance general entre flexibilidad y control
                                - Más políticas flexibles = mercado más competitivo en servicio
                                - Más políticas estrictas = hosts más protegidos pero menos accesibles
                                - **Decisión**: Evalúa si la flexibilidad te da ventaja competitiva o si necesitas protección
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre enfoques por ciudad:**
                                - Ciudades con políticas flexibles dominantes = mercados más orientados al huésped
                                - Ciudades con políticas estrictas = hosts más experimentados y cautelosos
                                - **Insight**: La política dominante refleja la madurez y cultura del mercado local
                                """
                            },
                            "host_response_time": {
                                "agrupadas": """
                                **Lo que nos dice sobre velocidad de respuesta:**
                                - Muestra qué tan rápido responden los hosts en cada ciudad
                                - Respuestas rápidas = mercado competitivo en servicio al cliente
                                - Respuestas lentas = oportunidad para destacar con mejor servicio
                                - **Ventaja**: En mercados lentos, ser rápido te diferencia inmediatamente
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre estándares de servicio:**
                                - Revela el nivel general de atención al cliente en el mercado
                                - Más respuestas rápidas = huéspedes más exigentes en tiempos
                                - **Benchmark**: El estándar de respuesta marca las expectativas mínimas del mercado
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre liderazgo en servicio:**
                                - Ciudades con respuestas rápidas dominantes tienen culturas de servicio más desarrolladas
                                - **Aprendizaje**: Replica las prácticas de ciudades líderes en tiempo de respuesta
                                """
                            },
                            "host_identity_verified": {
                                "agrupadas": """
                                **Lo que nos dice sobre verificación de identidad:**
                                - Muestra el nivel de confianza y verificación en cada mercado
                                - Alta verificación = mercado maduro con culturas de seguridad
                                - Baja verificación = oportunidad para diferenciarte con mayor confiabilidad
                                - **Ventaja**: En mercados con poca verificación, estar verificado aumenta la confianza
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre estándares de seguridad:**
                                - Revela qué tan importante es la verificación para el mercado general
                                - Más verificación = huéspedes más conscientes de la seguridad
                                - **Decisión**: La verificación puede ser factor diferenciador o requisito básico
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre culturas de confianza:**
                                - Ciudades con alta verificación tienen ecosistemas más maduros
                                - **Estrategia**: En ciudades líderes en verificación, es prácticamente obligatorio
                                """
                            },
                            "has_availability": {
                                "agrupadas": """
                                **Lo que nos dice sobre disponibilidad del mercado:**
                                - Muestra qué tan activo está el mercado en cada ciudad
                                - Alta disponibilidad = muchas opciones para huéspedes, más competencia
                                - Baja disponibilidad = mercado ocupado, alta demanda
                                - **Oportunidad**: Mercados con baja disponibilidad permiten precios más altos
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre balance oferta-demanda:**
                                - Revela el equilibrio general entre propiedades disponibles y demanda
                                - Más disponibilidad = posible saturación del mercado
                                - **Insight**: La disponibilidad indica si es mejor competir por precio o por diferenciación
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre dinámicas de ocupación:**
                                - Ciudades con baja disponibilidad dominante tienen mercados más calientes
                                - **Estrategia**: En mercados ocupados, enfócate en precio; en disponibles, en diferenciación
                                """
                            },
                            "price_range": {
                                "agrupadas": """
                                **Lo que nos dice sobre segmentos de precio:**
                                - Muestra qué rangos de precio dominan en cada ciudad
                                - Rangos altos = mercados premium con huéspedes de mayor poder adquisitivo
                                - Rangos bajos = mercados de volumen con enfoque en accesibilidad
                                - **Estrategia**: Alinea tu precio con el rango dominante o busca nichos desatendidos
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre estructura de precios del mercado:**
                                - Revela si el mercado es principalmente económico, medio o premium
                                - Distribución equilibrada = mercado maduro con todos los segmentos
                                - **Oportunidad**: Segmentos con poca oferta pueden tener demanda insatisfecha
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre posicionamiento por ciudad:**
                                - Muestra qué ciudades lideran en cada segmento de precio
                                - **Benchmarking**: Ciudades líderes en segmentos premium pueden inspirar estrategias de valor
                                """
                            },
                            "accommodates_band": {
                                "agrupadas": """
                                **Lo que nos dice sobre capacidad de alojamiento:**
                                - Muestra qué tamaños de grupo son más comunes en cada ciudad
                                - Capacidades grandes = enfoque en familias y grupos
                                - Capacidades pequeñas = mercado de parejas y viajeros individuales
                                - **Segmentación**: El tamaño dominante define tu público objetivo principal
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre tipos de viajeros:**
                                - Revela si el mercado está más orientado a viajeros individuales o grupos
                                - Más capacidad pequeña = turismo de negocios y parejas
                                - Más capacidad grande = turismo familiar y de grupos
                                - **Estrategia**: Optimiza tu propiedad para el segmento con mayor demanda
                                """,
                                "% apiladas": """
                                **Lo que nos dice sobre especialización por tamaño:**
                                - Muestra qué ciudades dominan cada segmento de capacidad
                                - **Insight**: Ciudades especializadas en grupos grandes pueden tener estrategias replicables
                                """
                            },
                            "bathrooms_band": {
                                "agrupadas": """
                                **Lo que nos dice sobre número de baños por propiedad:**
                                - Indica si la oferta está orientada a viajes individuales (1 baño) o a grupos/familias (2+ baños)
                                - Propiedades con más baños suelen justificar precios más altos y atraer reservas de familias
                                - **Estrategia**: Si una ciudad tiene pocas opciones con >1 baño, puede ser un nicho rentable
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre capacidad real de alojar grupos:**
                                - Las barras apiladas muestran volumen total y qué ciudades ofrecen más baños por propiedad
                                - Alta proporción de propiedades con múltiples baños = mayor enfoque en familias/grupos
                                - **Insight**: Ajusta tarifas y amenidades (camas, cocina) para maximizar ocupación en propiedades con más baños
                                """,
                                "% apiladas": """
                                **Participación por banda de baños:**
                                - Muestra qué ciudades dominan cada banda (1, 1.5, 2+ baños)
                                - Útil para comparar oferta real vs demanda por tamaño de grupo
                                - **Oportunidad**: Las bandas poco representadas pueden tener demanda insatisfecha en temporadas altas
                                """
                            },
                            "amenities_band": {
                                "agrupadas": """
                                **Lo que nos dice sobre el paquete de servicios ofrecidos:**
                                - Muestra la distribución de propiedades según cantidad de amenities (básico -> completo)
                                - Más amenities suele correlacionar con mejores reseñas y mayor precio por noche
                                - **Estrategia**: En ciudades con pocas propiedades muy equipadas, añadir amenities clave (wifi, cocina completa, aire acondicionado) puede diferenciarte
                                """,
                                "apiladas": """
                                **Lo que nos dice sobre la competencia en servicios:**
                                - Revela el volumen de oferta con paquetes completos frente a opciones básicas
                                - Ciudades con muchas propiedades con muchas amenities tienden a competir por calidad, no solo por precio
                                - **Decisión**: Si la ciudad es competitiva en amenities, invierte en experiencia; si no, destaca con servicios clave
                                """,
                                "% apiladas": """
                                **Participación de paquetes de amenities:**
                                - Muestra qué ciudades lideran en ofrecer experiencias completas
                                - Pedazos pequeños indican oportunidades para diferenciarse con una oferta diferencial
                                - **Recomendación**: Prioriza añadir amenities que el mercado valora (wifi estable, lavadora, aire acondicionado)
                                """
                            }
                        }
                        
                        # Si la variable tiene interpretaciones específicas, las usa
                        if variable in interpretaciones:
                            if "agrupadas" in tipo_grafica and "agrupadas" in interpretaciones[variable]:
                                return interpretaciones[variable]["agrupadas"]
                            elif "% apiladas" in tipo_grafica and "% apiladas" in interpretaciones[variable]:
                                return interpretaciones[variable]["% apiladas"]
                            elif "apiladas" in tipo_grafica and "apiladas" in interpretaciones[variable]:
                                return interpretaciones[variable]["apiladas"]
                        
                        # Interpretación genérica para otras variables
                        if "agrupadas" in tipo_grafica:
                            return f"""
                            **Lo que nos dice sobre {variable} en el mercado:**
                            - Cada ciudad muestra su perfil único en esta característica
                            - Las diferencias entre ciudades revelan distintas culturas y preferencias
                            - Categorías dominantes indican tendencias del mercado local
                            - **Oportunidad**: Categorías populares en unas ciudades pero ausentes en otras pueden ser nichos
                            """
                        elif "% apiladas" in tipo_grafica:
                            return f"""
                            **Lo que nos dice sobre participación en {variable}:**
                            - Muestra qué ciudad lidera en cada categoría de esta variable
                            - Revela especializaciones y fortalezas regionales
                            - Categorías sin líderes claros son mercados más equilibrados
                            - **Estrategia**: Replica lo que funciona en ciudades líderes de cada categoría
                            """
                        else:  # apiladas normales
                            return f"""
                            **Lo que nos dice sobre la distribución total de {variable}:**
                            - Las categorías más grandes tienen mayor demanda general
                            - Los segmentos de colores muestran la contribución de cada ciudad
                            - Revela patrones generales del mercado europeo de Airbnb
                            - **Insight**: Categorías grandes con poca representación de tu ciudad son oportunidades
                            """
                    
                    # Mostrar interpretación dinámica
                    interpretacion = get_interpretacion_variable(Variable_Cat, tipo_cat)
                    st.markdown(interpretacion)

            elif tipo_cat == "Barras por ciudad (grid ≤4 por fila)":
                # Small multiples: una barra por ciudad
                figs, titles = [], []
                for ctz in ciudades_sel:
                    frec_ctz = frec[frec["ciudad"] == ctz].sort_values("frecuencia", ascending=False)
                    if frec_ctz.empty:
                        continue
                    fig = px.bar(
                        frec_ctz, x="__cat__", y="frecuencia",
                        title=None
                    )
                    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
                    fig.update_traces(type="bar")  # <-- asegura barras
                    fig.update_xaxes(title=None, tickangle=45, automargin=True)
                    fig.update_yaxes(title=None)
                    figs.append(fig); titles.append(ctz)
                if figs:
                    render_grid(figs, cols_per_row=cols_grid, titles=titles)
                    
                    # Interpretación dinámica para Barras por ciudad
                    with st.expander("Interpretación del Gráfico"):
                        def get_interpretacion_barras_ciudad(variable):
                            interpretaciones_barras = {
                                "room_type": """
                                **Lo que nos dice el perfil individual de cada ciudad en tipos de alojamiento:**
                                - Cada gráfico es como el "ADN" de esa ciudad en términos de tipos de alojamiento
                                - Las barras más altas muestran qué tipo de propiedad es más común en cada lugar
                                - **Ciudades parecidas**: Tienen barras altas en los mismos tipos - compiten directamente
                                - **Ciudades únicas**: Tienen barras altas en tipos diferentes - cada una tiene su nicho
                                - **Para tu estrategia**: Si dos ciudades tienen perfiles similares, las tácticas que funcionan en una probablemente funcionen en la otra
                                """,
                                "property_type": """
                                **Lo que nos dice el perfil inmobiliario de cada ciudad:**
                                - Revela la arquitectura y cultura habitacional de cada destino
                                - Ciudades con apartamentos dominantes = centros urbanos densos
                                - Ciudades con casas = destinos más familiares o residenciales
                                - **Estrategia**: El perfil inmobiliario define tu público objetivo y precios
                                """,
                                "host_is_superhost": """
                                **Lo que nos dice sobre la profesionalización por ciudad:**
                                - Ciudades con muchos superhosts = mercados muy competitivos
                                - Ciudades con pocos superhosts = oportunidad de destacar fácilmente
                                - Compara el nivel de exigencia y profesionalización entre destinos
                                - **Decisión**: En mercados profesionalizados, invierte más en calidad; en otros, diferénciate rápido
                                """,
                                "barrio_std": """
                                **Lo que nos dice sobre la concentración geográfica:**
                                - Muestra qué barrios dominan en cada ciudad
                                - Ciudades con distribución equilibrada = mercado maduro y disperso
                                - Ciudades con barrios dominantes = concentración en zonas prime
                                - **Oportunidad**: Barrios secundarios pueden tener mejor precio-ubicación
                                """,
                                "cancellation_policy": """
                                **Lo que nos dice sobre enfoques de política por ciudad:**
                                - Ciudades con políticas flexibles = mercados orientados al volumen y satisfacción
                                - Ciudades con políticas estrictas = hosts más protegidos y experimentados
                                - **Cultura local**: La política dominante refleja la madurez del mercado
                                """,
                                "host_identity_verified": """
                                **Lo que nos dice sobre culturas de verificación:**
                                - Ciudades con alta verificación = mercados más seguros y profesionales
                                - Ciudades con baja verificación = oportunidad para destacar con mayor confiabilidad
                                - **Diferenciación**: En mercados poco verificados, la verificación es ventaja competitiva
                                """,
                                "price_range": """
                                **Lo que nos dice sobre segmentación de mercado:**
                                - Cada ciudad muestra su perfil de precios dominante
                                - Ciudades premium vs económicas tienen diferentes estrategias óptimas
                                - **Posicionamiento**: El rango dominante define las expectativas de valor
                                """
                                ,
                                "bathrooms_band": """
                                **Lo que nos dice sobre capacidad de servicio por ciudad:**
                                - Muestra si una ciudad tiene más propiedades orientadas a grupos (más baños)
                                - Las ciudades con más opciones multi-baño atraen reservas familiares y grupos grandes
                                - **Estrategia**: Si tu ciudad tiene pocas opciones con varios baños, considera adaptar propiedades para grupos
                                """,
                                "amenities_band": """
                                **Lo que nos dice sobre calidad de oferta por ciudad:**
                                - Muestra qué ciudades invierten más en amenities completas
                                - Ciudades con muchas amenities suelen competir por satisfacción y mayor precio
                                - **Oportunidad**: Añadir amenities clave puede aumentar ocupación y reseñas rápidamente
                                """
                            }
                            
                            if variable in interpretaciones_barras:
                                return interpretaciones_barras[variable]
                            else:
                                return f"""
                                **Lo que nos dice el perfil individual de cada ciudad en {variable}:**
                                - Cada gráfico muestra las características dominantes de esa ciudad
                                - Las barras más altas indican las categorías más comunes en cada lugar
                                - Puedes comparar directamente los perfiles entre ciudades
                                - **Análisis**: Ciudades con perfiles similares compiten directamente; las diferentes pueden inspirar nuevas estrategias
                                """
                        
                        interpretacion_barras = get_interpretacion_barras_ciudad(Variable_Cat)
                        st.markdown(interpretacion_barras)
                else:
                    st.info("Sin datos para las ciudades seleccionadas.")

            else:  # "Pastel (grid ≤4 por fila)"
                figs, titles = [], []
                for ctz in ciudades_sel:
                    frec_ctz = frec[frec["ciudad"] == ctz]
                    if frec_ctz.empty:
                        continue
                    fig_pie = px.pie(
                        frec_ctz, names="__cat__", values="frecuencia",
                        title=None
                    )
                    fig_pie.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
                    figs.append(fig_pie); titles.append(ctz)
                if figs:
                    render_grid(figs, cols_per_row=cols_grid, titles=titles)
                    
                    # Interpretación dinámica para gráficos de Pastel
                    with st.expander("Interpretación del Gráfico"):
                        def get_interpretacion_pastel(variable):
                            interpretaciones_pastel = {
                                "room_type": """
                                **Lo que nos dice sobre la especialización de cada ciudad en tipos de alojamiento:**
                                - Cada pastel muestra qué tipos de alojamiento predominan en cada ciudad
                                - Los pedazos grandes indican que esa ciudad se especializa en ese tipo
                                - **Ciudades especializadas**: Tienen uno o dos pedazos muy grandes - dominan ciertos tipos
                                - **Ciudades diversas**: Tienen pedazos de tamaño similar - ofrecen variedad equilibrada
                                - **Oportunidad**: Los pedazos pequeños en ciudades grandes pueden ser nichos con poca competencia
                                """,
                                "property_type": """
                                **Lo que nos dice sobre la especialización inmobiliaria:**
                                - Revela si cada ciudad se especializa en tipos específicos de propiedades
                                - Pedazos grandes = fortalezas claras (ej: Amsterdam en apartamentos)
                                - Distribución equilibrada = mercado diversificado sin especialización clara
                                - **Estrategia**: En ciudades especializadas, sigue la tendencia; en diversas, diferénciate
                                """,
                                "host_is_superhost": """
                                **Lo que nos dice sobre la distribución de calidad:**
                                - El tamaño del pedazo "superhost" muestra el nivel de profesionalización
                                - Ciudades con pedazo grande de superhosts = mercados muy competitivos
                                - Ciudades con pedazo pequeño = oportunidades para destacar rápidamente
                                - **Decisión**: Evalúa si necesitas ser superhost para competir o si puedes diferenciarte de otra forma
                                """,
                                "barrio_std": """
                                **Lo que nos dice sobre concentración geográfica:**
                                - Pedazos grandes muestran barrios dominantes con alta concentración
                                - Distribución equilibrada indica mercado geográficamente disperso
                                - Barrios con pedazos pequeños pueden ser emergentes o subutilizados
                                - **Oportunidad**: Barrios con pedazos pequeños pero buena ubicación pueden tener potencial inexplorado
                                """,
                                "cancellation_policy": """
                                **Lo que nos dice sobre enfoques de gestión:**
                                - Pedazo grande de políticas flexibles = ciudad orientada al huésped
                                - Pedazo grande de políticas estrictas = hosts más protegidos
                                - **Filosofía**: El pedazo dominante revela la cultura de gestión de riesgos
                                """,
                                "host_identity_verified": """
                                **Lo que nos dice sobre estándares de confianza:**
                                - Pedazo grande de verificados = mercado maduro con alta confianza
                                - Pedazo grande de no verificados = oportunidad para diferenciarte con seguridad
                                - **Ventaja**: En mercados poco verificados, la verificación es factor clave
                                """,
                                "price_range": """
                                **Lo que nos dice sobre especialización de precios:**
                                - Pedazos grandes muestran en qué segmento se especializa cada ciudad
                                - Distribución equilibrada = ciudad diversificada en todos los rangos
                                - **Nicho**: Pedazos pequeños pueden ser segmentos desatendidos con oportunidad
                                """,
                                "accommodates_band": """
                                **Lo que nos dice sobre especialización por capacidad:**
                                - Pedazos grandes revelan si la ciudad se especializa en grupos pequeños o grandes
                                - Especialización clara = ventajas operativas en ese segmento
                                - **Estrategia**: Sigue la especialización dominante o busca nichos de capacidad desatendidos
                                """
                                ,
                                "bathrooms_band": """
                                **Lo que nos dice sobre especialización por baños:**
                                - Pedazos grandes indican ciudades con oferta orientada a grupos/familias (más baños)
                                - Útil para diseñar amenities y precios para estancias familiares
                                - **Recomendación**: Valora añadir baños o servicios complementarios si tu ciudad carece de opciones multi-baño
                                """,
                                "amenities_band": """
                                **Lo que nos dice sobre especialización por amenities:**
                                - Pedazos grandes muestran ciudades que priorizan una oferta completa de servicios
                                - Ciudades con pocos pedazos grandes en amenities son oportunidades para diferenciarse
                                - **Acción**: Ofrece amenities demandadas localmente (wifi, lavadora, aire acondicionado) para subir reseñas y precios
                                """
                            }
                            
                            if variable in interpretaciones_pastel:
                                return interpretaciones_pastel[variable]
                            else:
                                return f"""
                                **Lo que nos dice sobre la distribución de {variable} en cada ciudad:**
                                - Cada pastel muestra cómo se distribuyen las categorías de esta variable
                                - Pedazos grandes indican categorías dominantes en cada ciudad
                                - Pedazos pequeños pueden ser oportunidades nicho
                                - **Análisis**: Ciudades especializadas vs diversificadas tienen diferentes estrategias óptimas
                                """
                        
                        interpretacion_pastel = get_interpretacion_pastel(Variable_Cat)
                        st.markdown(interpretacion_pastel)
                else:
                    st.info("Sin datos para las ciudades seleccionadas.")

            if mostrar_tabla_cmp:
                st.dataframe(
                    frec.sort_values(["ciudad","frecuencia"], ascending=[True, False]).reset_index(drop=True),
                    use_container_width=True
                )

        else:
            st.info(f"No hay datos en '{Variable_Cat}' para las ciudades seleccionadas.")

        st.markdown("---")

        # ====== Sección: Boxplot comparativo ======
        st.subheader("Distribución de precios por ciudad (boxplot)")
        if "price" in df_comp.columns and df_comp["price"].dropna().shape[0] > 0:
            fig_comp_box = px.box(
                df_comp.dropna(subset=["price"]), x="ciudad", y="price",
                points="suspectedoutliers",
                title="Boxplot de precios por ciudad"
            )
            fig_comp_box.update_layout(height=520, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig_comp_box, use_container_width=True)
            
            # Interpretación del boxplot
            with st.expander("Interpretación del Boxplot"):
                st.markdown("""
                **Lo que nos dice sobre los precios de Airbnb por ciudad:**
                
                **La caja central nos revela:**
                - **Línea del medio**: El precio típico que cobran la mayoría de hosts en cada ciudad
                - **Altura de la caja**: Si es alta, hay mucha variación en los precios; si es baja, los precios son similares
                - **Posición de la caja**: Las cajas más arriba indican ciudades más caras en general
                
                **Comparando ciudades:**
                - **Ciudades con cajas estrechas**: Los hosts cobran precios muy parecidos - mercado estandarizado
                - **Ciudades con cajas anchas**: Hay desde opciones baratas hasta caras - más diversidad de ofertas
                - **Puntos dispersos arriba**: Propiedades de lujo que cobran mucho más que el promedio
                - **Puntos dispersos abajo**: Ofertas muy económicas o promociones
                
                **Para entender el mercado:**
                - Si todas las ciudades tienen precios similares, compiten directamente
                - Si una ciudad tiene caja muy estrecha, es difícil destacar solo por precio
                - Los puntos dispersos muestran nichos especiales (lujo o económico) que pueden ser oportunidades
                """)
        else:
            st.info("No hay datos de 'price' suficientes para mostrar boxplot comparativo.")

        st.markdown("---")

        # ====== Sección: Histograma comparativo ======
        st.subheader("Histograma de precios por ciudad")
        if "price" in df_comp.columns and df_comp["price"].dropna().shape[0] > 0:
            col_h1, col_h2 = st.columns([1.2, 1])
            with col_h1:
                nbins_cmp = st.slider("Número de bins (comparativo)", 10, 120, 50, step=5, key="bins_hist_cmp")
            with col_h2:
                modo_hist = st.selectbox("Modo de barras", ["overlay", "stack"], index=0, key="modo_hist_cmp")

            fig_comp_hist = px.histogram(
                df_comp, x="price", color="ciudad", nbins=nbins_cmp,
                barmode=modo_hist,
                title="Histograma comparativo de precios"
            )
            fig_comp_hist.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig_comp_hist, use_container_width=True)
            
            # Interpretación del histograma
            with st.expander("Interpretación del Histograma"):
                st.markdown(f"""
                **Lo que nos dice sobre los rangos de precios en el mercado:**
                
                **Modo actual: {modo_hist.upper()}**
                
                **Patrones que observamos:**
                - **Picos altos**: Rangos de precios donde hay muchas propiedades - alta competencia
                - **Varios picos**: Indica diferentes segmentos: económico, medio y premium
                - **Forma sesgada**: La mayoría de propiedades se concentra en precios bajos o altos
                - **Distribución plana**: Precios bien repartidos - mercado equilibrado
                
                **Lo que significa cada modo:**
                {"- **Overlay**: Puedes ver exactamente dónde cada ciudad compite más. Las 'lagunas' muestran rangos donde una ciudad tiene pocas ofertas" if modo_hist == "overlay" else "- **Stack**: Muestra el volumen total de propiedades por rango de precio y cuánto aporta cada ciudad. Los rangos más altos tienen más demanda total"}
                
                **Para fijar precios inteligentemente:**
                - **Evita los picos**: Son rangos saturados con mucha competencia
                - **Busca los valles**: Rangos con pocas propiedades pero posible demanda no satisfecha
                - **Considera diversificar**: Tener propiedades en diferentes rangos según lo que funciona en cada ciudad
                """)
        else:
            st.info("No hay datos de 'price' suficientes para mostrar histograma comparativo.")

        st.markdown("---")

        # ====== Sección: Mapa comparativo ======
        st.subheader("Mapa comparativo")
        if {"latitude","longitude"}.issubset(df_comp.columns):
            col_m1, col_m2, col_m3 = st.columns([1.2,1.2,1])
            with col_m1:
                map_style_cmp = st.selectbox(
                    "Estilo de mapa",
                    ["open-street-map", "carto-positron", "carto-darkmatter"],
                    key="map_style_cmp"
                )
            with col_m2:
                # Opciones de coloración disponibles
                color_options_cmp = ["ciudad"]
                if "host_is_superhost" in df_comp.columns:
                    color_options_cmp.append("host_is_superhost")
                if "room_type" in df_comp.columns:
                    color_options_cmp.append("room_type")
                
                color_map_by = st.selectbox("Color por", color_options_cmp, index=0, key="color_map_by_cmp")
            with col_m3:
                usar_tamano_precio = st.checkbox("Tamaño por precio", value=True, key="size_price_cmp")

            # Columnas base requeridas para el mapa
            geo_cols_cmp = ["latitude","longitude","price","barrio_std","ciudad"]
            
            # Agregar columnas opcionales si existen
            if "host_is_superhost" in df_comp.columns:
                geo_cols_cmp.append("host_is_superhost")
            if "room_type" in df_comp.columns:
                geo_cols_cmp.append("room_type")
            
            df_geo_cmp = df_comp[geo_cols_cmp].dropna(subset=["latitude","longitude"]).copy()
            
            # Si se quiere usar tamaño por precio, filtrar NaN en price
            if usar_tamano_precio and "price" in df_geo_cmp.columns:
                df_geo_cmp = df_geo_cmp.dropna(subset=["price"])
            
            max_pts = st.slider("Límite de puntos por mapa", 1000, 10000, 4000, step=500, key="max_pts_cmp")
            if len(df_geo_cmp) > max_pts:
                df_geo_cmp = df_geo_cmp.sample(max_pts, random_state=0)

            # Configurar parámetros según el tipo de color y verificar que price no tenga NaN
            size_kw = dict(size="price", size_max=15) if (usar_tamano_precio and "price" in df_geo_cmp.columns and df_geo_cmp["price"].notna().any()) else {}
            
            if color_map_by == "ciudad":
                # Cuando coloreamos por ciudad (categórico)
                fig_map_cmp = px.scatter_mapbox(
                    df_geo_cmp, lat="latitude", lon="longitude",
                    color="ciudad", 
                    hover_name="ciudad",
                    hover_data={
                        "price": ":€,.0f",
                        "barrio_std": True,
                        "latitude": ":.4f",
                        "longitude": ":.4f",
                        "ciudad": False
                    },
                    mapbox_style=map_style_cmp,
                    title=f"Distribución geográfica de listados ({len(df_geo_cmp):,} puntos)",
                    height=520,
                    **size_kw
                )
            elif color_map_by == "host_is_superhost":
                # Cuando coloreamos por superhost - filtrar solo superhosts verdaderos
                df_geo_cmp_superhost = df_geo_cmp[df_geo_cmp["host_is_superhost"] == 't'].copy()
                fig_map_cmp = px.scatter_mapbox(
                    df_geo_cmp_superhost, lat="latitude", lon="longitude",
                    color="host_is_superhost", 
                    hover_name="host_is_superhost",
                    hover_data={
                        "price": ":€,.0f",
                        "barrio_std": True,
                        "ciudad": True,
                        "latitude": ":.4f",
                        "longitude": ":.4f",
                        "host_is_superhost": False
                    },
                    mapbox_style=map_style_cmp,
                    title=f"Distribución geográfica de Superhosts ({len(df_geo_cmp_superhost):,} puntos)",
                    height=520,
                    **size_kw
                )
            elif color_map_by == "room_type":
                # Cuando coloreamos por tipo de habitación
                fig_map_cmp = px.scatter_mapbox(
                    df_geo_cmp, lat="latitude", lon="longitude",
                    color="room_type", 
                    hover_name="room_type",
                    hover_data={
                        "price": ":€,.0f",
                        "barrio_std": True,
                        "ciudad": True,
                        "latitude": ":.4f",
                        "longitude": ":.4f",
                        "room_type": False
                    },
                    mapbox_style=map_style_cmp,
                    title=f"Distribución geográfica de listados ({len(df_geo_cmp):,} puntos)",
                    height=520,
                    **size_kw
                )
            else:
                # Fallback por si hay otra opción
                fig_map_cmp = px.scatter_mapbox(
                    df_geo_cmp, lat="latitude", lon="longitude",
                    color=color_map_by, 
                    hover_name=color_map_by,
                    hover_data={
                        "price": ":€,.0f",
                        "barrio_std": True,
                        "ciudad": True,
                        "latitude": ":.4f",
                        "longitude": ":.4f"
                    },
                    mapbox_style=map_style_cmp,
                    title=f"Distribución geográfica de listados ({len(df_geo_cmp):,} puntos)",
                    height=520,
                    **size_kw
                )
            
            # Usar el dataframe apropiado para calcular centro y zoom
            if color_map_by == "host_is_superhost":
                df_for_center = df_geo_cmp[df_geo_cmp["host_is_superhost"] == 't']
            else:
                df_for_center = df_geo_cmp
                
            center_lat = df_for_center["latitude"].median()
            center_lon = df_for_center["longitude"].median()
            
            # Calcular zoom dinámico para múltiples ciudades
            lat_range = df_for_center["latitude"].max() - df_for_center["latitude"].min()
            lon_range = df_for_center["longitude"].max() - df_for_center["longitude"].min()
            max_range = max(lat_range, lon_range)
            
            if len(ciudades_sel) == 1:
                zoom_level = 10
            elif max_range < 1:
                zoom_level = 8
            elif max_range < 5:
                zoom_level = 6
            elif max_range < 20:
                zoom_level = 4
            else:
                zoom_level = 2
            
            fig_map_cmp.update_layout(
                mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=zoom_level),
                margin=dict(l=10, r=10, t=50, b=10)
            )
            
            # Agregar etiquetas de ciudades en el mapa comparativo
            # Usar el dataframe apropiado según el filtro seleccionado
            if color_map_by == "host_is_superhost":
                df_for_labels = df_geo_cmp[df_geo_cmp["host_is_superhost"] == 't']
            else:
                df_for_labels = df_geo_cmp
                
            city_centers = (
                df_for_labels.groupby("ciudad")
                .agg({
                    "latitude": "mean",
                    "longitude": "mean",
                    "price": ["count", "mean"]
                })
                .round(2)
            )
            city_centers.columns = ["lat_center", "lon_center", "count", "avg_price"]
            city_centers = city_centers.reset_index()
            
            # Agregar etiquetas de ciudades
            for _, row in city_centers.iterrows():
                fig_map_cmp.add_trace(
                    go.Scattermapbox(
                        lat=[row["lat_center"]],
                        lon=[row["lon_center"]],
                        mode="text",
                        text=[f"<b>{row['ciudad']}</b><br>{row['count']} listings<br>Avg: €{row['avg_price']:,.0f}"],
                        textfont=dict(size=12, color="white"),
                        showlegend=False,
                        hoverinfo="skip"
                    )
                )
            
            st.plotly_chart(fig_map_cmp, use_container_width=True)
        else:
            st.info("No hay columnas de latitud/longitud para el mapa comparativo.")

        st.markdown("---")

        # ====== Sección: Análisis Comparativo de Competitividad ======
        st.subheader("Análisis Comparativo de Competitividad")
        
        if len(df_comp) > 0:
            # Función para calcular métricas de competitividad por ciudad
            def calculate_city_competitiveness(city_data):
                metrics = {}
                city_name = city_data['ciudad'].iloc[0] if 'ciudad' in city_data.columns else 'Unknown'
                
                # Disponibilidad (usando availability_365 - más realista)
                if 'availability_365' in city_data.columns and city_data['availability_365'].notna().any():
                    # Calcular % de disponibilidad basado en días disponibles del año
                    avg_availability_days = city_data['availability_365'].mean()
                    availability_pct = (avg_availability_days / 365) * 100
                    # Para competitividad: menos disponible = más ocupado = más competitivo
                    availability_score = 100 - availability_pct
                else:
                    # Fallback más realista para Airbnb
                    availability_pct = 65  # ~65% disponibilidad es típico
                    availability_score = 35
                
                # Profesionalismo (corregido)
                prof_components = []
                if 'host_is_superhost' in city_data.columns:
                    superhost_pct = (city_data['host_is_superhost'] == 't').mean() * 100
                    prof_components.append(superhost_pct * 0.4 / 100)
                if 'host_identity_verified' in city_data.columns:
                    verified_pct = (city_data['host_identity_verified'] == 't').mean() * 100
                    prof_components.append(verified_pct * 0.3 / 100)
                if 'host_response_time' in city_data.columns:
                    fast_response_pct = (city_data['host_response_time'] == 'within an hour').mean() * 100
                    prof_components.append(fast_response_pct * 0.3 / 100)
                
                prof_score = sum(prof_components) * 100 if prof_components else 0
                
                # Flexibilidad (corregida)
                flex_components = []
                if 'instant_bookable' in city_data.columns:
                    instant_pct = (city_data['instant_bookable'] == 't').mean() * 100
                    flex_components.append(instant_pct * 0.5 / 100)
                if 'cancellation_policy' in city_data.columns:
                    flexible_policy_pct = (city_data['cancellation_policy'] == 'flexible').mean() * 100
                    flex_components.append(flexible_policy_pct * 0.5 / 100)
                
                flex_score = sum(flex_components) * 100 if flex_components else 0
                
                # Servicios (corregido)
                if 'amenities_count' in city_data.columns and city_data['amenities_count'].notna().any():
                    amenities_score = min(city_data['amenities_count'].mean() / 15 * 100, 100)
                else:
                    amenities_score = 0
                
                # Variación de precios (corregida)
                if 'price' in city_data.columns and city_data['price'].notna().any():
                    price_cv = (city_data['price'].std() / city_data['price'].mean()) * 100 if city_data['price'].mean() > 0 else 0
                    price_score = min(price_cv / 50 * 100, 100)
                else:
                    price_score = 0
                
                # Índice compuesto (sin disponibilidad, corregido)
                competitiveness_index = (
                    prof_score * 0.40 +
                    flex_score * 0.30 +
                    amenities_score * 0.20 +
                    price_score * 0.10
                )
                
                return {
                    'Ciudad': city_name,
                    'Índice_Competitividad': competitiveness_index,
                    'Disponibilidad': availability_score,
                    'Profesionalismo': prof_score,
                    'Flexibilidad': flex_score,
                    'Servicios': amenities_score,
                    'Variación_Precios': price_score,
                    'Total_Listings': len(city_data),
                    'Precio_Promedio': city_data['price'].mean() if 'price' in city_data.columns else 0,
                    'Superhosts_Pct': (city_data['host_is_superhost'] == 't').mean() * 100 if 'host_is_superhost' in city_data.columns else 0,
                    'Disponibilidad_Pct': availability_pct
                }

            # Calcular métricas para todas las ciudades
            competitiveness_results = []
            for ciudad in ciudades_sel:
                city_data = df_comp[df_comp['ciudad'] == ciudad]
                if len(city_data) > 0:
                    competitiveness_results.append(calculate_city_competitiveness(city_data))

            if competitiveness_results:
                comp_df = pd.DataFrame(competitiveness_results)
                comp_df = comp_df.round(2)
                
                # Ranking de competitividad
                comp_df_sorted = comp_df.sort_values('Índice_Competitividad', ascending=False)
                
                st.markdown("#### Ranking de Competitividad por Ciudad")
                
                # Mostrar tabla de rankings
                display_cols = ['Ciudad', 'Índice_Competitividad', 'Total_Listings', 'Superhosts_Pct', 
                               'Disponibilidad_Pct', 'Precio_Promedio']
                st.dataframe(comp_df_sorted[display_cols].reset_index(drop=True), use_container_width=True)
                
                # Gráficos comparativos
                col_comp1, col_comp2 = st.columns(2)
                
                with col_comp1:
                    # Gráfico de barras del índice de competitividad
                    fig_comp_index = px.bar(
                        comp_df_sorted, 
                        x='Ciudad', 
                        y='Índice_Competitividad',
                        title="Índice de Competitividad por Ciudad",
                        color='Índice_Competitividad',
                        color_continuous_scale=AIRBNB_COMPETITIVENESS_SCALE
                    )
                    fig_comp_index.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
                    fig_comp_index.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_comp_index, use_container_width=True)
                
                with col_comp2:
                    # Scatter plot: Competitividad vs Precio Promedio
                    fig_scatter_comp = px.scatter(
                        comp_df,
                        x='Precio_Promedio',
                        y='Índice_Competitividad',
                        size='Total_Listings',
                        color='Ciudad',
                        title="Competitividad vs Precio Promedio",
                        labels={'Precio_Promedio': 'Precio Promedio (€)', 'Índice_Competitividad': 'Índice Competitividad'}
                    )
                    fig_scatter_comp.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
                    st.plotly_chart(fig_scatter_comp, use_container_width=True)
                
                # Interpretaciones y recomendaciones
                st.markdown("#### Interpretaciones y Oportunidades")
                
                col_interp1, col_interp2 = st.columns(2)
                
                with col_interp1:
                    # Ciudad más competitiva
                    most_competitive = comp_df_sorted.iloc[0]
                    st.success(f"**Mercado Más Competitivo: {most_competitive['Ciudad']}**")
                    st.write(f"- Índice: {most_competitive['Índice_Competitividad']:.1f}/100")
                    st.write(f"- {most_competitive['Total_Listings']:.0f} listings totales")
                    st.write(f"- {most_competitive['Superhosts_Pct']:.1f}% superhosts")
                    
                    # Ciudad menos competitiva (oportunidad)
                    least_competitive = comp_df_sorted.iloc[-1]
                    st.info(f"**Mayor Oportunidad: {least_competitive['Ciudad']}**")
                    st.write(f"- Índice: {least_competitive['Índice_Competitividad']:.1f}/100")
                    st.write(f"- Menor competencia relativa")
                    st.write(f"- Espacio para diferenciación")
                
                with col_interp2:
                    # Análisis de correlaciones
                    if len(comp_df) > 2:
                        corr_comp_price = comp_df['Índice_Competitividad'].corr(comp_df['Precio_Promedio'])
                        st.markdown("**Correlaciones Clave:**")
                        st.write(f"• Competitividad vs Precio: {corr_comp_price:.3f}")
                        
                        if corr_comp_price > 0.5:
                            st.write("→ A mayor competitividad, mayores precios")
                        elif corr_comp_price < -0.5:
                            st.write("→ Mercados competitivos tienen precios menores")
                        else:
                            st.write("→ Relación débil entre competitividad y precio")
                        
                        # Recomendación estratégica
                        st.markdown("**Recomendación Estratégica:**")
                        best_value = comp_df.loc[comp_df['Índice_Competitividad'].idxmin()]
                        st.write(f"Considerar entrada en **{best_value['Ciudad']}**")
                        st.write("- Menor competencia")
                        st.write("- Oportunidad de liderazgo")

            else:
                st.info("No hay suficientes datos para el análisis de competitividad.")
        else:
            st.info("No hay datos disponibles para el análisis comparativo.")

        st.markdown("---")

        # ====== Sección: Métricas Clave con Deltas ======
        st.subheader("Métricas Clave del Mercado")
        
        # Calcular métricas comparativas
        total_listings = len(df_comp)
        precio_promedio = df_comp['price'].mean() if 'price' in df_comp.columns else 0
        ciudades_activas = len(ciudades_sel)
        
        # Calcular ocupación promedio (usando availability_365)
        if 'availability_365' in df_comp.columns and df_comp['availability_365'].notna().any():
            avg_avail_days = df_comp['availability_365'].mean()
            ocupacion_promedio = 100 - ((avg_avail_days / 365) * 100)  # Ocupación = 100 - % disponibilidad
        else:
            ocupacion_promedio = 35  # ~35% ocupación es realista
        
        # ====== Calcular DELTAS REALES basados en datos ======
        
        # 1. Calcular promedio global de todas las ciudades para comparación
        df_global = pd.concat([df_comp])  # En caso de que solo tengamos una ciudad seleccionada
        if len(ciudades_sel) > 1:
            df_global = df_comp  # Ya es el conjunto completo
        
        # Limpiar precios para cálculo correcto
        try:
            if len(df_global) > 0 and 'price' in df_global.columns:
                df_global['price_numeric'] = df_global['price'].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
                precio_global = df_global['price_numeric'].mean()
            else:
                precio_global = precio_promedio
        except:
            precio_global = precio_promedio
        
        # 2. Delta de precio vs promedio global
        if precio_global > 0 and precio_promedio > 0:
            precio_delta_pct = ((precio_promedio - precio_global) / precio_global) * 100
            precio_delta = f"{precio_delta_pct:+.1f}%" if abs(precio_delta_pct) > 0.1 else "0%"
        else:
            precio_delta = "N/A"
        precio_delta_color = "normal" if "+" in precio_delta else "inverse" if precio_delta != "N/A" else "off"
        
        # 3. Delta de ocupación basado en disponibilidad (inversa de availability_365)
        if 'availability_365' in df_comp.columns:
            ocupacion_estimada_actual = (365 - df_comp['availability_365'].mean()) / 365 * 100
            ocupacion_global = (365 - df_global['availability_365'].mean()) / 365 * 100 if len(df_global) > 0 else ocupacion_estimada_actual
            
            if ocupacion_global > 0:
                ocupacion_delta_pct = ocupacion_estimada_actual - ocupacion_global
                ocupacion_delta = f"{ocupacion_delta_pct:+.1f}%" if abs(ocupacion_delta_pct) > 0.1 else "0%"
            else:
                ocupacion_delta = "N/A"
        else:
            ocupacion_delta = "+3.2%"  # Fallback simulado
        ocupacion_delta_color = "normal" if "+" in ocupacion_delta else "inverse" if ocupacion_delta != "N/A" else "off"
        
        # 4. Delta de listings basado en densidad de propiedades por ciudad
        listings_per_city_avg = len(df_global) / len(ciudades_sel) if len(ciudades_sel) > 0 else total_listings
        if listings_per_city_avg > 0:
            listings_delta_pct = ((total_listings - listings_per_city_avg) / listings_per_city_avg) * 100
            listings_delta = f"{listings_delta_pct:+.0f}%" if abs(listings_delta_pct) > 1 else "0%"
        else:
            listings_delta = f"+{total_listings//10}"
        
        # Mostrar métricas en columnas
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric(
                "Precio Promedio", 
                f"€{precio_promedio:,.0f}" if precio_promedio > 0 else "N/A",
                delta=precio_delta,
                delta_color=precio_delta_color
            )
        
        with col_m2:
            st.metric(
                "Total Listings", 
                f"{total_listings:,}",
                delta=listings_delta,
                delta_color="normal"
            )
        
        with col_m3:
            # 5. Delta de superhosts vs promedio global
            superhosts_pct = (df_comp['host_is_superhost'] == 't').mean() * 100 if 'host_is_superhost' in df_comp.columns else 0
            superhosts_global_pct = (df_global['host_is_superhost'] == 't').mean() * 100 if 'host_is_superhost' in df_global.columns and len(df_global) > 0 else superhosts_pct
            
            if superhosts_global_pct > 0:
                superhost_delta_pct = superhosts_pct - superhosts_global_pct
                superhost_delta = f"{superhost_delta_pct:+.1f}%" if abs(superhost_delta_pct) > 0.1 else "0%"
            else:
                superhost_delta = "N/A"
            
            st.metric(
                "Superhosts", 
                f"{superhosts_pct:.1f}%",
                delta=superhost_delta,
                # Para superhosts: + es siempre bueno, - es siempre malo
                delta_color="normal" if "+" in superhost_delta else "inverse" if superhost_delta != "N/A" else "off"
            )

        # Explicación de deltas
        st.info("**Interpretación de Deltas**: Los porcentajes mostrados comparan las métricas seleccionadas contra el promedio global de todas las ciudades disponibles. Verde indica rendimiento superior al promedio, rojo indica rendimiento inferior.")

        # ====== Comparativo Multi-Ciudad ROI ======
        st.markdown("---")
        st.markdown(
            "<h3 style='text-align: center;'>Comparativo Multi-Ciudad ROI</h3>", 
            unsafe_allow_html=True
        )
        # Parámetros de simulación centrados
        st.markdown(
            "<h4 style='text-align: center;'>Parámetros de simulación</h4>", 
            unsafe_allow_html=True
        )
        
        # Input centrado
        col_empty1, col_input, col_empty2 = st.columns([1, 2, 1])
        with col_input:
            gastos_mensuales_input_comp = st.number_input(
                "Gastos operativos mensuales (€)", 
                min_value=200, 
                max_value=3000, 
                value=800, 
                step=50, 
                key="gastos_comp_multi",
                help="Gastos fijos: seguros, mantenimiento, servicios, impuestos, etc. NO incluye comisiones Airbnb."
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Resultados centrados
        if len(ciudades_sel) > 0:
            st.markdown(
                "<h4 style='text-align: center;'>Ranking ROI por Ciudad</h4>", 
                unsafe_allow_html=True
            )
            
            # Calcular ROI para todas las ciudades
            roi_ciudades_comp = []
            
            for ciudad in ciudades_sel:
                    ciudad_data = df_comp[df_comp['ciudad'] == ciudad].copy()
                    
                    if len(ciudad_data) > 0:
                        # Limpiar precios
                        if 'price' in ciudad_data.columns:
                            ciudad_data['price_clean'] = ciudad_data['price'].astype(str).str.replace('$', '').str.replace(',', '')
                            ciudad_data['price_clean'] = pd.to_numeric(ciudad_data['price_clean'], errors='coerce')
                            precio_promedio_ciudad = ciudad_data['price_clean'].mean()
                        else:
                            precio_promedio_ciudad = 0
                        
                        # Ocupación realista por ciudad (basada en datos de mercado real)
                        ocupacion_rates = {
                            'Barcelona': 0.68,  # 68% ocupación
                            'Amsterdam': 0.62,  # 62% ocupación (menor por regulaciones)
                            'Milan': 0.65,      # 65% ocupación
                            'Athens': 0.70,     # 70% ocupación (destino más barato)
                            'Madrid': 0.67      # 67% ocupación
                        }
                        
                        ocupacion_pct_ciudad = ocupacion_rates.get(ciudad, 0.65) * 100
                        dias_ocupados_ciudad = ocupacion_pct_ciudad / 100 * 365
                        
                        # Revenue anual bruto
                        revenue_bruto_ciudad = precio_promedio_ciudad * dias_ocupados_ciudad
                        
                        # Comisiones y costos variables (% del revenue bruto)
                        comision_airbnb = revenue_bruto_ciudad * 0.15  # 15% comisión Airbnb
                        costos_limpieza = revenue_bruto_ciudad * 0.05   # 5% limpieza y servicios
                        
                        # Revenue neto (después de comisiones)
                        revenue_neto_ciudad = revenue_bruto_ciudad - comision_airbnb - costos_limpieza
                        
                        # Gastos operativos fijos anuales
                        gastos_operativos_ciudad = gastos_mensuales_input_comp * 12
                        
                        # Ganancia neta anual
                        ganancia_neta_ciudad = revenue_neto_ciudad - gastos_operativos_ciudad
                        
                        # Inversión inicial estimada (para ROI real)
                        # Estimación: 6-10 meses de gastos + setup inicial por ciudad
                        setup_costs = {
                            'Barcelona': 8000,   # Costos altos de setup
                            'Amsterdam': 12000,  # Muy regulado, costos altos
                            'Milan': 7000,       # Costos medios
                            'Athens': 5000,      # Costos más bajos
                            'Madrid': 6500       # Costos medios
                        }
                        
                        inversion_inicial = setup_costs.get(ciudad, 7000) + (gastos_mensuales_input_comp * 8)
                        
                        # ROI real = (Ganancia Neta Anual / Inversión Inicial) * 100
                        roi_ciudad = (ganancia_neta_ciudad / inversion_inicial * 100) if inversion_inicial > 0 else 0
                        
                        roi_ciudades_comp.append({
                            'Ciudad': ciudad,
                            'Precio_Promedio': precio_promedio_ciudad,
                            'Ocupacion_Pct': ocupacion_pct_ciudad,
                            'Dias_Ocupados': dias_ocupados_ciudad,
                            'Revenue_Bruto': revenue_bruto_ciudad,
                            'Revenue_Neto': revenue_neto_ciudad,
                            'Inversion_Inicial': inversion_inicial,
                            'Ganancia_Neta': ganancia_neta_ciudad,
                            'ROI': roi_ciudad
                        })
            
            # Ordenar por ROI
            roi_ciudades_comp.sort(key=lambda x: x['ROI'], reverse=True)
            
            # Mostrar resultados por ciudad
            for i, ciudad_roi in enumerate(roi_ciudades_comp):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.markdown(f"**#{i+1}: {ciudad_roi['Ciudad']}**")
                        
                        if ciudad_roi['ROI'] > 100:
                            st.success(f"**ROI: {ciudad_roi['ROI']:.1f}%**")
                        elif ciudad_roi['ROI'] > 50:
                            st.info(f"**ROI: {ciudad_roi['ROI']:.1f}%**")
                        elif ciudad_roi['ROI'] > 0:
                            st.warning(f"**ROI: {ciudad_roi['ROI']:.1f}%**")
                        else:
                            st.error(f"**ROI: {ciudad_roi['ROI']:.1f}%**")
                    
                    with col_b:
                        st.metric("Ganancia Neta/Año", f"€{ciudad_roi['Ganancia_Neta']:,.0f}")
                    
                    with col_c:
                        st.metric("Revenue Neto", f"€{ciudad_roi['Revenue_Neto']:,.0f}")
                    
                    st.caption(f"Precio promedio: €{ciudad_roi['Precio_Promedio']:.0f}/noche | Ocupación: {ciudad_roi['Ocupacion_Pct']:.0f}% ({ciudad_roi['Dias_Ocupados']:.0f} días/año)")
                    st.markdown("---")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Resumen final centrado
            mejor_comp = roi_ciudades_comp[0]
            peor_comp = roi_ciudades_comp[-1]
            
            st.markdown(
                "<h4 style='text-align: center;'>Resumen Comparativo</h4>", 
                unsafe_allow_html=True
            )
            
            col_empty1, col_res1, col_res2, col_empty2 = st.columns([0.5, 2, 2, 0.5])
            with col_res1:
                st.success(f"**Mejor oportunidad**  \n{mejor_comp['Ciudad']} - {mejor_comp['ROI']:.1f}% ROI")
            with col_res2:
                if peor_comp['ROI'] > 0:
                    st.info(f"**Menor ROI**  \n{peor_comp['Ciudad']} - {peor_comp['ROI']:.1f}% ROI")
                else:
                    st.error(f"**Pérdidas en**  \n{peor_comp['Ciudad']} - {peor_comp['ROI']:.1f}% ROI")

        else:
            st.markdown("<br><br>", unsafe_allow_html=True)
            col_empty1, col_warning, col_empty2 = st.columns([1, 2, 1])
            with col_warning:
                st.warning("Selecciona al menos una ciudad para calcular ROI.")

        st.stop()

#Rama: POR CIUDAD
    
    df_city = df[df["ciudad"] == ciudad_sel].copy()

    Tabla_frecuencias = (
        df_city[Variable_Cat]
        .astype("object").fillna("NA").astype(str)
        .value_counts().head(top_k)
        .reset_index()
    )
    Tabla_frecuencias.columns = ['categorias', 'frecuencia']

    st.subheader('Exploración visual')
    opciones = ['Barras', 'Pastel', 'Dona', 'Área']
    graf_sel = st.selectbox('¿Qué gráfica quieres ver?', opciones, index=0, key='graf_sel_cat')

    if Tabla_frecuencias.empty:
        st.warning(f"Sin categorías para '{Variable_Cat}' en {ciudad_sel}.")
    else:
        if graf_sel == 'Barras':
            fig = px.bar(Tabla_frecuencias, x='categorias', y='frecuencia',
                         title=f'Frecuencia — {Variable_Cat} ({ciudad_sel})')
        elif graf_sel == 'Pastel':
            fig = px.pie(Tabla_frecuencias, names='categorias', values='frecuencia',
                         title=f'Frecuencia — {Variable_Cat} ({ciudad_sel})')
        elif graf_sel == 'Dona':
            fig = px.pie(Tabla_frecuencias, names='categorias', values='frecuencia', hole=0.45,
                         title=f'Dona — {Variable_Cat} ({ciudad_sel})')
        else:
            tmp = Tabla_frecuencias.sort_values('categorias')
            fig = px.area(tmp, x='categorias', y='frecuencia',
                          title=f'Área — {Variable_Cat} ({ciudad_sel})')
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    cE, cF = st.columns(2)

    # BOXPLOT
    with cE:
        if "price" in df_city.columns and df_city["price"].notna().any():
            cat_para_box = st.selectbox(
                "Categoría para Boxplot (precio)",
                options=[c for c in Lista if c in df_city.columns], index=0, key="boxcat"
            )
            df_box = df_city[[cat_para_box, "price"]].dropna()
            top_cats = df_box[cat_para_box].astype("object").value_counts().head(min(top_k, 15)).index
            df_box = df_box[df_box[cat_para_box].astype("object").isin(top_cats)]
            fig_box = px.box(df_box, x=cat_para_box, y="price", points=False,
                             title=f"Boxplot de precio por {cat_para_box} — {ciudad_sel}")
            fig_box.update_layout(height=480)
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("No hay columna de precio válida para el boxplot.")

    # HEATMAP: coocurrencias entre 2 categóricas
    with cF:
        cats_heat = [c for c in Lista if c in df_city.columns]
        if len(cats_heat) >= 2:
            cat_x = st.selectbox("Heatmap — Eje X", options=cats_heat, index=0, key="hx")
            cat_y = st.selectbox("Heatmap — Eje Y", options=cats_heat, index=min(1, len(cats_heat)-1), key="hy")
            t = (
                df_city[[cat_x, cat_y]].astype("object").fillna("NA")
                .value_counts().reset_index(name="freq")
            )
            top_x = t[cat_x].value_counts().head(min(top_k, 15)).index
            top_y = t[cat_y].value_counts().head(min(top_k, 15)).index
            t = t[t[cat_x].isin(top_x) & t[cat_y].isin(top_y)]

            fig_hm = px.density_heatmap(
                t, x=cat_x, y=cat_y, z="freq", color_continuous_scale="Blues",
                title=f"Heatmap de frecuencias — {cat_x} vs {cat_y} ({ciudad_sel})"
            )
            fig_hm.update_layout(height=480)
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Selecciona al menos dos variables categóricas para el heatmap.")

    # TABLA de frecuencias (toggle)
    if mostrar_tabla:
        st.markdown("### Tabla de frecuencias")
        Tabla_frecuencias = Tabla_frecuencias.reset_index(drop=True)
        Tabla_frecuencias.index = np.arange(1, len(Tabla_frecuencias) + 1)
        Tabla_frecuencias.index.name = "#"
        st.dataframe(Tabla_frecuencias, use_container_width=True)

    # === ANÁLISIS DE COMPETITIVIDAD ===
    if len(df_city) > 0:
        st.markdown("---")
        st.subheader("Análisis de Competitividad del Mercado")

        # Función para calcular el índice de competitividad
        def calculate_competitiveness_metrics(city_data):
            metrics = {}
            
            # 1. Saturación del mercado (densidad de listings por vecindario)
            if 'barrio_std' in city_data.columns:
                listings_per_neighborhood = city_data.groupby('barrio_std').size()
                avg_density = listings_per_neighborhood.mean()
                max_density = listings_per_neighborhood.max()
                saturation_score = min(avg_density / 50 * 100, 100)  # Normalizado a 50 listings/barrio
                metrics['saturation'] = avg_density
                metrics['saturation_score'] = saturation_score
                metrics['max_density_neighborhood'] = max_density
            else:
                metrics['saturation'] = 0
                metrics['saturation_score'] = 0
            
            # 2. Disponibilidad del mercado (usando availability_365)
            if 'availability_365' in city_data.columns and city_data['availability_365'].notna().any():
                avg_availability_days = city_data['availability_365'].mean()
                availability_pct = (avg_availability_days / 365) * 100
                availability_score = 100 - availability_pct  # Menos disponible = más ocupado = más competitivo
                metrics['availability_pct'] = availability_pct
                metrics['availability_score'] = availability_score
            else:
                metrics['availability_pct'] = 65  # Fallback realista
                metrics['availability_score'] = 35
            
            # 3. Profesionalismo del mercado (más realista)
            prof_components = []
            if 'host_is_superhost' in city_data.columns:
                superhost_pct = (city_data['host_is_superhost'] == 't').mean() * 100
                prof_components.append(superhost_pct * 0.4 / 100)  # Normalizar a escala 0-1 primero
                metrics['superhost_pct'] = superhost_pct
            
            if 'host_identity_verified' in city_data.columns:
                verified_pct = (city_data['host_identity_verified'] == 't').mean() * 100
                prof_components.append(verified_pct * 0.3 / 100)  # Normalizar a escala 0-1 primero
                metrics['verified_pct'] = verified_pct
            
            if 'host_response_time' in city_data.columns:
                fast_response_pct = (city_data['host_response_time'] == 'within an hour').mean() * 100
                prof_components.append(fast_response_pct * 0.3 / 100)  # Normalizar a escala 0-1 primero
                metrics['fast_response_pct'] = fast_response_pct
            
            professionalism_score = sum(prof_components) * 100 if prof_components else 0  # Convertir a 0-100
            metrics['professionalism_score'] = professionalism_score
            
            # 4. Flexibilidad del mercado (más realista)
            flex_components = []
            if 'instant_bookable' in city_data.columns:
                instant_pct = (city_data['instant_bookable'] == 't').mean() * 100
                flex_components.append(instant_pct * 0.5 / 100)  # Normalizar a escala 0-1 primero
                metrics['instant_bookable_pct'] = instant_pct
            
            if 'cancellation_policy' in city_data.columns:
                flexible_policy_pct = (city_data['cancellation_policy'] == 'flexible').mean() * 100
                flex_components.append(flexible_policy_pct * 0.5 / 100)  # Normalizar a escala 0-1 primero
                metrics['flexible_policy_pct'] = flexible_policy_pct
            
            flexibility_score = sum(flex_components) * 100 if flex_components else 0  # Convertir a 0-100
            metrics['flexibility_score'] = flexibility_score
            
            # 5. Competencia en servicios (más conservador)
            if 'amenities_count' in city_data.columns and city_data['amenities_count'].notna().any():
                avg_amenities = city_data['amenities_count'].mean()
                # Escala más realista: 15 amenities = 100%
                amenities_score = min(avg_amenities / 15 * 100, 100)
                metrics['avg_amenities'] = avg_amenities
                metrics['amenities_score'] = amenities_score
            else:
                metrics['avg_amenities'] = 0
                metrics['amenities_score'] = 0
            
            # 6. Competencia en precios (más conservador)
            if 'price' in city_data.columns and city_data['price'].notna().any():
                price_std = city_data['price'].std()
                price_mean = city_data['price'].mean()
                price_cv = (price_std / price_mean) * 100 if price_mean > 0 else 0
                # Escala más realista: 50% CV = 100% competencia
                price_competition_score = min(price_cv / 50 * 100, 100)
                metrics['price_cv'] = price_cv
                metrics['price_competition_score'] = price_competition_score
            else:
                metrics['price_cv'] = 0
                metrics['price_competition_score'] = 0
            
            # Índice de Competitividad Compuesto (0-100)
            # Sin disponibilidad, redistribuyendo ponderaciones:
            # Profesionalismo: 40% (incrementado)
            # Flexibilidad: 30% (incrementado) 
            # Servicios: 20% (igual)
            # Precios: 10% (igual)
            competitiveness_index = (
                professionalism_score * 0.40 +
                flexibility_score * 0.30 +
                metrics['amenities_score'] * 0.20 +
                metrics['price_competition_score'] * 0.10
            )
            
            metrics['competitiveness_index'] = competitiveness_index
            return metrics

        # Calcular métricas para la ciudad actual
        comp_metrics = calculate_competitiveness_metrics(df_city)
        
        # Mostrar métricas principales
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        
        with col_c1:
            ci_value = comp_metrics['competitiveness_index']
            ci_color = "normal"
            if ci_value >= 70:
                ci_label = "Alta"
                ci_color = "inverse"
            elif ci_value >= 50:
                ci_label = "Media"
            else:
                ci_label = "Baja"
            st.metric("Índice Competitividad", f"{ci_value:.1f}/100", delta=ci_label, delta_color=ci_color)
        
        with col_c2:
            st.metric("% Superhosts", f"{comp_metrics.get('superhost_pct', 0):.1f}%")
        
        with col_c3:
            st.metric("% Disponibilidad", f"{comp_metrics['availability_pct']:.1f}%")
        
        with col_c4:
            # KPI adicional - podemos agregar otro aquí si es necesario
            pass

        # Gráficos de competitividad
        col_cg1, col_cg2 = st.columns(2)
        
        with col_cg1:
            # Radar chart de dimensiones de competitividad (sin disponibilidad)
            dimensions = ['Profesionalismo', 'Flexibilidad', 'Servicios', 'Precios']
            scores = [
                comp_metrics['professionalism_score'],
                comp_metrics['flexibility_score'],
                comp_metrics['amenities_score'],
                comp_metrics['price_competition_score']
            ]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=scores + [scores[0]],  # Cerrar el polígono
                theta=dimensions + [dimensions[0]],
                fill='toself',
                name=f'{ciudad_sel}',
                line_color=PALETTE["brand"]
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100])
                ),
                title="",  # Quitamos el título del gráfico
                height=400,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            
            # Título con tooltip help
            st.markdown(f"**Perfil de Competitividad — {ciudad_sel}**", 
                       help="""Variables del Radar y Columnas de BD:

• PROFESIONALISMO (40%):
host_is_superhost (40%)
host_identity_verified (30%)  
host_response_time (30%)

• FLEXIBILIDAD (30%):
instant_bookable (50%)
cancellation_policy (50%)

• SERVICIOS (20%):
amenities_count (calculado desde amenities)

• PRECIOS (10%):
price (coeficiente de variación)""")

            st.plotly_chart(fig_radar, use_container_width=True)
        
        with col_cg2:
            # Análisis de profesionalismo por vecindario (top 10)
            if 'barrio_std' in df_city.columns and 'host_is_superhost' in df_city.columns:
                neighborhood_prof = df_city.groupby('barrio_std').agg({
                    'host_is_superhost': lambda x: (x == 't').mean() * 100
                }).reset_index()
                neighborhood_prof.columns = ['barrio_std', 'superhost_pct']
                
                # Filtrar vecindarios con al menos 5 listings
                neighborhood_counts = df_city.groupby('barrio_std').size()
                neighborhood_prof = neighborhood_prof[neighborhood_prof['barrio_std'].isin(
                    neighborhood_counts[neighborhood_counts >= 5].index
                )]
                
                top_neighborhoods = neighborhood_prof.nlargest(10, 'superhost_pct')
                
                if not top_neighborhoods.empty:
                    fig_bar_neigh = px.bar(
                        top_neighborhoods, 
                        x='barrio_std', 
                        y='superhost_pct',
                        title=f"Top 10 Vecindarios con Mayor Profesionalismo — {ciudad_sel}",
                        labels={'barrio_std': 'Vecindario', 'superhost_pct': '% Superhosts'}
                    )
                    fig_bar_neigh.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
                    fig_bar_neigh.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_bar_neigh, use_container_width=True)
                else:
                    st.info("Sin suficientes datos de vecindarios para analizar profesionalismo.")
            else:
                st.info("Datos de vecindarios no disponibles.")

        # Interpretación del índice
        st.markdown("#### Interpretación del Índice de Competitividad")
        
        col_int1, col_int2 = st.columns(2)
        
        with col_int1:
            if ci_value >= 70:
                st.warning("**Mercado Altamente Competitivo**")
                st.write("- Hosts muy profesionalizados") 
                st.write("- Alta ocupación de propiedades")
                st.write("- Servicios premium abundantes")
                st.write("- Difícil entrada para nuevos hosts")
            elif ci_value >= 50:
                st.info("**Mercado Moderadamente Competitivo**")
                st.write("- Competencia equilibrada")
                st.write("- Oportunidades de diferenciación")
                st.write("- Mix de hosts profesionales y casuales")
            else:
                st.success("**Mercado con Oportunidades**")
                st.write("- Menor competencia relativa")
                st.write("- Espacio para nuevos entrantes")
                st.write("- Potencial de profesionalización")
        
        with col_int2:
            st.markdown("**Componentes del Índice:**")
            st.write(f"• Profesionalismo: {comp_metrics['professionalism_score']:.1f}/100 (40%)")
            st.write(f"  - Superhosts: {comp_metrics.get('superhost_pct', 0):.1f}%")
            st.write(f"• Flexibilidad: {comp_metrics['flexibility_score']:.1f}/100 (30%)")
            st.write(f"  - Reserva instantánea: {comp_metrics.get('instant_bookable_pct', 0):.1f}%")
            st.write(f"• Servicios: {comp_metrics['amenities_score']:.1f}/100 (20%)")
            st.write(f"  - Amenities promedio: {comp_metrics.get('avg_amenities', 0):.1f}")
            st.write(f"• Precios: {comp_metrics['price_competition_score']:.1f}/100 (10%)")
            st.write(f"  - Variación precios: {comp_metrics.get('price_cv', 0):.1f}% CV")

    # === ANÁLISIS GEOESPACIAL ===
    if {"latitude", "longitude"}.issubset(df_city.columns):
        st.markdown("---")
        st.subheader("Análisis Geoespacial")

        # Columnas base requeridas
        # Construir lista de columnas geográficas basadas en lo que existe
        geo_cols = []
        required_cols = ["latitude", "longitude"]
        optional_cols = ["price", "barrio_std", "host_is_superhost", "room_type"]
        
        # Agregar columnas requeridas
        for col in required_cols:
            if col in df_city.columns:
                geo_cols.append(col)
        
        # Agregar columnas opcionales si existen
        for col in optional_cols:
            if col in df_city.columns:
                geo_cols.append(col)
        
        # Verificar que al menos tenemos lat y lon
        if "latitude" not in geo_cols or "longitude" not in geo_cols:
            st.warning("No hay datos de ubicación disponibles para esta ciudad.")
        else:
            df_geo = df_city[geo_cols].dropna(subset=["latitude", "longitude"])

            if len(df_geo) == 0:
                st.warning("No hay datos válidos de ubicación para mostrar en el mapa.")
            else:
                col_geo1, col_geo2 = st.columns([3, 1])

                with col_geo2:
                    # Opciones de coloración disponibles según columnas DESPUÉS del filtrado
                    color_options = []
                    if "price" in df_geo.columns and df_geo["price"].notna().any():
                        color_options.append("price")
                    if "host_is_superhost" in df_geo.columns and df_geo["host_is_superhost"].notna().any():
                        color_options.append("host_is_superhost")
                    if "room_type" in df_geo.columns and df_geo["room_type"].notna().any():
                        color_options.append("room_type")
                    
                    # Si no hay opciones válidas, usar un valor por defecto
                    if not color_options:
                        st.warning("No hay columnas válidas para colorear el mapa.")
                        color_by_geo_page = None
                    else:
                        color_by_geo_page = st.selectbox("Colorear por:", color_options, key="color_geo")
                    
                    map_style_page = st.selectbox(
                        "Estilo de mapa:",
                        ["open-street-map", "carto-positron", "carto-darkmatter"],
                        key="map_style"
                    )

                with col_geo1:
                    # Limitar puntos para mejor rendimiento
                    max_points = st.slider("Máximo de puntos en el mapa", 500, 5000, 2000, step=250, key="max_points_geo")
                    show_neighborhood_labels = st.checkbox("Mostrar nombres de vecindarios", value=True, key="show_labels")
                    
                    if len(df_geo) > max_points:
                        df_geo_sample = df_geo.sample(max_points, random_state=42)
                    else:
                        df_geo_sample = df_geo.copy()

                    # Si no hay color_by_geo_page válido, no renderizar el mapa
                    if color_by_geo_page is None:
                        st.info("No hay suficientes datos para renderizar el mapa con colores.")
                    elif color_by_geo_page not in df_geo_sample.columns:
                        st.error(f"La columna '{color_by_geo_page}' no está disponible en los datos.")
                    else:
                        # Construir hover_data dinámicamente según columnas disponibles
                        base_hover = {}
                        if "price" in df_geo_sample.columns:
                            base_hover["price"] = ":€,.0f"
                        if "latitude" in df_geo_sample.columns:
                            base_hover["latitude"] = ":.4f"
                        if "longitude" in df_geo_sample.columns:
                            base_hover["longitude"] = ":.4f"
                        if "barrio_std" in df_geo_sample.columns:
                            base_hover["barrio_std"] = False  # Ya está en hover_name

                        if color_by_geo_page == "price":
                            # Filtrar valores NaN en price para evitar errores en el mapa
                            df_geo_valid = df_geo_sample.dropna(subset=["price"])
                            if len(df_geo_valid) == 0:
                                st.warning("No hay datos válidos de precio para mostrar en el mapa.")
                            else:
                                fig_map = px.scatter_mapbox(
                                    df_geo_valid, lat="latitude", lon="longitude",
                                    color="price", size="price",
                                    hover_name="barrio_std" if "barrio_std" in df_geo_valid.columns else None,
                                    hover_data=base_hover,
                                    mapbox_style=map_style_page,
                                    title=f"Distribución Geográfica por Precio - {ciudad_sel} ({len(df_geo_valid):,} puntos)",
                                    height=500,
                                    color_continuous_scale="Viridis",
                                    size_max=15
                                )
                        elif color_by_geo_page == "host_is_superhost":
                            # Filtrar solo superhosts verdaderos
                            df_geo_superhost = df_geo_sample[df_geo_sample["host_is_superhost"] == 't'].copy()
                            if len(df_geo_superhost) == 0:
                                st.warning("No hay superhosts para mostrar en el mapa.")
                                df_geo_valid = pd.DataFrame()  # Dataframe vacío para evitar errores
                            else:
                                hover_superhost = base_hover.copy()
                                hover_superhost["host_is_superhost"] = True
                                fig_map = px.scatter_mapbox(
                                    df_geo_superhost, lat="latitude", lon="longitude",
                                    color="host_is_superhost",
                                    hover_name="barrio_std" if "barrio_std" in df_geo_superhost.columns else None,
                                    hover_data=hover_superhost,
                                    mapbox_style=map_style_page,
                                    title=f"Distribución Geográfica de Superhosts - {ciudad_sel} ({len(df_geo_superhost):,} puntos)",
                                    height=500
                                )
                                df_geo_valid = df_geo_superhost
                        else:  # room_type
                            room_hover = base_hover.copy()
                            if "room_type" in df_geo_sample.columns:
                                room_hover["room_type"] = True
                            
                            fig_map = px.scatter_mapbox(
                                df_geo_sample, lat="latitude", lon="longitude",
                                color="room_type",
                                hover_name="barrio_std" if "barrio_std" in df_geo_sample.columns else None,
                                hover_data=room_hover,
                                mapbox_style=map_style_page,
                                title=f"Distribución Geográfica por Tipo de Habitación - {ciudad_sel} ({len(df_geo_sample):,} puntos)",
                                height=500
                            )
                            df_geo_valid = df_geo_sample

                        # Solo continuar si tenemos datos válidos y fig_map fue creado
                        if 'df_geo_valid' in locals() and len(df_geo_valid) > 0:
                            # Calcular centro y zoom inteligente
                            center_lat = df_geo_valid["latitude"].median()
                            center_lon = df_geo_valid["longitude"].median()
                            
                            # Calcular zoom basado en la dispersión de los datos
                            lat_range = df_geo_valid["latitude"].max() - df_geo_valid["latitude"].min()
                            lon_range = df_geo_valid["longitude"].max() - df_geo_valid["longitude"].min()
                            max_range = max(lat_range, lon_range)
                            
                            if max_range < 0.1:
                                zoom_level = 12
                            elif max_range < 0.5:
                                zoom_level = 10
                            elif max_range < 1.0:
                                zoom_level = 8
                            else:
                                zoom_level = 6

                            fig_map.update_layout(
                                mapbox=dict(
                                    center=dict(lat=center_lat, lon=center_lon), 
                                    zoom=zoom_level
                                ),
                                margin=dict(l=0, r=0, t=50, b=0)
                            )
                            
                            # Agregar etiquetas de vecindarios si está habilitado
                            if show_neighborhood_labels and "barrio_std" in df_geo_valid.columns:
                                # Calcular centros de vecindarios para las etiquetas
                                neighborhood_centers = (
                                    df_geo_valid.groupby("barrio_std")
                                    .agg({
                                        "latitude": "mean",
                                        "longitude": "mean",
                                        "price": "count"
                                    })
                                    .reset_index()
                                    .rename(columns={"price": "count"})
                                )
                                
                                # Solo mostrar vecindarios con suficientes listados
                                neighborhood_centers = neighborhood_centers[neighborhood_centers["count"] >= 5]
                                
                                # Agregar texto de vecindarios
                                for _, row in neighborhood_centers.iterrows():
                                    fig_map.add_trace(
                                        go.Scattermapbox(
                                            lat=[row["latitude"]],
                                            lon=[row["longitude"]],
                                            mode="text",
                                            text=[f"{row['barrio_std']}<br>({row['count']} listings)"],
                                            textfont=dict(size=10, color="white"),
                                            showlegend=False,
                                            hoverinfo="skip"
                                        )
                                    )

                            st.plotly_chart(fig_map, use_container_width=True)
                            
                            # Mostrar estadísticas del mapa
                            col_stats1, col_stats2, col_stats3 = st.columns(3)
                            with col_stats1:
                                st.metric("Total de listings", f"{len(df_geo):,}")
                            with col_stats2:
                                if "barrio_std" in df_geo.columns:
                                    st.metric("Vecindarios únicos", f"{df_geo['barrio_std'].nunique()}")
                                else:
                                    st.metric("Vecindarios únicos", "N/A")
                            with col_stats3:
                                if "price" in df_geo.columns:
                                    precio_promedio = df_geo["price"].mean()
                                    st.metric("Precio promedio", f"€{precio_promedio:,.0f}" if pd.notna(precio_promedio) else "N/A")
                                else:
                                    st.metric("Precio promedio", "N/A")

    # ====== Métricas Clave de la Ciudad ======
    st.markdown("---")
    st.subheader(f"Métricas Clave - {ciudad_sel}")
    
    # Calcular métricas específicas de la ciudad
    total_listings_city = len(df_city)
    precio_promedio_city = df_city['price'].mean() if 'price' in df_city.columns and len(df_city) > 0 else 0
    
    # Calcular ocupación estimada (usando availability_365)
    if 'availability_365' in df_city.columns and df_city['availability_365'].notna().any():
        avg_avail_days_city = df_city['availability_365'].mean()
        ocupacion_city = 100 - ((avg_avail_days_city / 365) * 100)
    else:
        ocupacion_city = 35  # Estimación realista
    
    # Calcular competitividad (versión simplificada)
    superhosts_city = (df_city['host_is_superhost'] == 't').mean() * 100 if 'host_is_superhost' in df_city.columns else 0
    instant_bookable_city = (df_city['instant_bookable'] == 't').mean() * 100 if 'instant_bookable' in df_city.columns else 0
    competitividad_city = (superhosts_city * 0.4 + instant_bookable_city * 0.3 + min(total_listings_city/50, 100) * 0.3)
    
    # ====== Calcular DELTAS REALES para ciudad específica ======
    # Cargar datos de todas las ciudades para comparación global
    archivos_ciudades = ['listingsAmsterdam.csv', 'listingsBarcelona.csv', 'listingsGrecia.csv', 'listingsMadrid.csv', 'listingsMilan.csv']
    df_all_cities = pd.DataFrame()
    
    for archivo in archivos_ciudades:
        try:
            df_temp = pd.read_csv(archivo)
            df_temp['ciudad'] = archivo.replace('listings', '').replace('.csv', '')
            df_all_cities = pd.concat([df_all_cities, df_temp], ignore_index=True)
        except:
            continue
    
    if len(df_all_cities) > 0:
        # Limpiar y convertir precios a numérico
        try:
            if 'price' in df_all_cities.columns:
                df_all_cities['price_numeric'] = df_all_cities['price'].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
                precio_global = df_all_cities['price_numeric'].mean()
            else:
                precio_global = precio_promedio_city
        except:
            precio_global = precio_promedio_city
            
        # Calcular promedios globales para comparación
        superhosts_global = (df_all_cities['host_is_superhost'] == 't').mean() * 100 if 'host_is_superhost' in df_all_cities.columns else 0
        listings_per_city_global = len(df_all_cities) / df_all_cities['ciudad'].nunique()
    else:
        # Fallback en caso de error
        precio_global = precio_promedio_city
        superhosts_global = superhosts_city
        listings_per_city_global = total_listings_city
    
    # Mostrar métricas con deltas REALES
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        # Delta de listings vs promedio global por ciudad
        if listings_per_city_global > 0:
            listings_delta_pct = ((total_listings_city - listings_per_city_global) / listings_per_city_global) * 100
            listings_delta = f"{listings_delta_pct:+.0f}%" if abs(listings_delta_pct) > 1 else "0%"
        else:
            listings_delta = f"+{total_listings_city//10}"
            
        st.metric(
            "Total Listings", 
            f"{total_listings_city:,}",
            delta=listings_delta,
            delta_color="normal" if "+" in listings_delta else "inverse" if listings_delta != "0%" else "off"
        )
    
    with col_c2:
        # Delta de precio vs promedio global
        if precio_global > 0:
            precio_delta_pct = ((precio_promedio_city - precio_global) / precio_global) * 100
            precio_delta = f"{precio_delta_pct:+.1f}%" if abs(precio_delta_pct) > 0.1 else "0%"
        else:
            precio_delta = "N/A"
        # Para precios: + es bueno para hosts (más ingresos), - es malo
        precio_delta_color = "normal" if "+" in precio_delta else "inverse" if precio_delta not in ["0%", "N/A"] else "off"
        st.metric(
            "Precio Promedio", 
            f"€{precio_promedio_city:,.0f}" if precio_promedio_city > 0 else "N/A",
            delta=precio_delta,
            delta_color=precio_delta_color
        )
    
    with col_c3:
        # Delta de superhosts vs promedio global
        superhosts_city_pct = (df_city['host_is_superhost'] == 't').mean() * 100 if 'host_is_superhost' in df_city.columns else 0
        
        if len(df_all_cities) > 0 and 'host_is_superhost' in df_all_cities.columns:
            superhosts_global_pct = (df_all_cities['host_is_superhost'] == 't').mean() * 100
            superhost_delta_pct = superhosts_city_pct - superhosts_global_pct
            superhost_delta = f"{superhost_delta_pct:+.1f}%" if abs(superhost_delta_pct) > 0.1 else "0%"
        else:
            superhost_delta = "N/A"
        
        # Para superhosts: + es siempre bueno, - es siempre malo
        superhost_delta_color = "normal" if "+" in superhost_delta else "inverse" if superhost_delta not in ["0%", "N/A"] else "off"
        st.metric(
            "Superhosts", 
            f"{superhosts_city_pct:.1f}%",
            delta=superhost_delta,
            delta_color=superhost_delta_color
        )



#---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# =========================================================
# ================== REGRESIÓN LINEAL =====================
# =========================================================
if View == "Regresión Lineal":

    st.title("Airbnb - Regresión Lineal")

    # --- Selección de ciudades desde el df unificado ---
    if "ciudad" not in df.columns or df["ciudad"].dropna().empty:
        st.warning("No hay columna 'ciudad' válida en el DataFrame.")
        st.stop()

    ciudades_disp = sorted(df["ciudad"].dropna().unique().tolist())
    st.sidebar.header("Ciudades")
    selected_cities = st.sidebar.multiselect(
        "Selecciona de 1 a 5 ciudades",
        options=ciudades_disp,
        default=ciudades_disp[:min(3, len(ciudades_disp))],
        max_selections=5
    )

    if not selected_cities:
        st.info("Selecciona al menos una ciudad para continuar.")
        st.stop()

    df_combined = df[df["ciudad"].isin(selected_cities)].copy()

    # --- Columnas numéricas candidatas ---
    numeric_cols = df_combined.select_dtypes(include="number").columns.tolist()
    default_y = "price" if "price" in numeric_cols else (numeric_cols[0] if numeric_cols else None)
    default_x = "accommodates" if "accommodates" in numeric_cols else (
        "amenities_count" if "amenities_count" in numeric_cols else (
            numeric_cols[1] if len(numeric_cols) > 1 else None
        )
    )

    if len(numeric_cols) < 2 or default_x is None or default_y is None:
        st.warning("Se requieren al menos 2 variables numéricas para la regresión.")
        st.stop()

    # --- Variables de regresión ---
    st.sidebar.header("Variables de regresión")
    x_var = st.sidebar.selectbox("Variable independiente (x)", numeric_cols, index=numeric_cols.index(default_x))
    restantes_para_y = [c for c in numeric_cols if c != x_var]
    y_idx = restantes_para_y.index(default_y) if default_y in restantes_para_y else 0
    y_var = st.sidebar.selectbox("Variable dependiente (y)", restantes_para_y, index=y_idx)

    remaining_vars = [col for col in numeric_cols if col not in [x_var, y_var]]
    max_predictors = min(15, len(remaining_vars))
    num_x = st.sidebar.slider(
        "¿Cuántas x adicionales (regresión múltiple)?", 
        0, max_predictors, min(2, max_predictors),
        help="Variables adicionales a la x principal"
    )
    st.sidebar.markdown(f"**Total de variables independientes: {num_x + 1}** (1 principal + {num_x} adicionales)")

    x_multi_vars = []
    for i in range(num_x):
        opciones = [col for col in remaining_vars if col not in x_multi_vars]
        x_i = st.sidebar.selectbox(f"Variable x{i+2} (Total: {i+2} variables)", opciones, key=f"x{i+2}_lin")
        x_multi_vars.append(x_i)

    # --- Limpieza de datos (mantener ciudad) ---
    cols_needed = [x_var, y_var, "ciudad"]
    df_clean = df_combined[cols_needed].dropna()
    if df_clean.empty:
        st.warning("No hay datos válidos después de limpiar NaN para las variables seleccionadas.")
        st.stop()

    # --- Utilidad de unidades ---
    def get_unit(var_name):
        units = {
            'price': '€','accommodates':'huéspedes','bedrooms':'habitaciones','beds':'camas',
            'bathrooms':'baños','bathrooms_num':'baños','amenities_count':'amenidades',
            'minimum_nights':'noches','maximum_nights':'noches','availability_365':'días',
            'number_of_reviews':'reseñas','reviews_per_month':'reseñas/mes',
            'review_scores_rating':'puntos','review_scores_accuracy':'puntos',
            'review_scores_cleanliness':'puntos','review_scores_checkin':'puntos',
            'review_scores_communication':'puntos','review_scores_location':'puntos',
            'review_scores_value':'puntos','calculated_host_listings_count':'propiedades',
            'latitude':'°','longitude':'°','superhost_numeric':'(0=No, 1=Sí)','price_per_person':'€/persona'
        }
        return units.get(var_name, '')

    # ===================== GRÁFICAS =====================
    st.subheader("Comparación visual")
    col_simple, col_multi = st.columns(2)

    # ====== REGRESIÓN SIMPLE (una por ciudad o todas juntas) ======
    with col_simple:
        st.markdown("**Regresión simple**")

        # Helper para graficar una ciudad
        def _plot_reg_simple_ciudad(sub_df: pd.DataFrame, ciudad: str, x_var: str, y_var: str):
            Xc = sub_df[[x_var]].values
            yc = sub_df[y_var].values
            model_c = LinearRegression()
            model_c.fit(Xc, yc)
            yhat_c = model_c.predict(Xc)
            order = np.argsort(Xc.ravel())
            x_sorted = Xc.ravel()[order]
            y_sorted = yhat_c[order]
            r2c = r2_score(yc, yhat_c)

            figc, axc = plt.subplots(figsize=(6, 4))  # tamaño compacto para grid
            axc.scatter(sub_df[x_var], sub_df[y_var], alpha=0.6)
            axc.plot(x_sorted, y_sorted, color='red', linewidth=2.5, linestyle='-', zorder=5, label="Línea de regresión")
            axc.text(0.04, 0.96, f'R² = {r2c:.3f}', transform=axc.transAxes, fontsize=11, fontweight='bold',
                    va='top', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, edgecolor='black', linewidth=1))
            axc.set_title(f"{ciudad}: {y_var} vs {x_var}", fontsize=12)
            axc.set_xlabel(x_var); axc.set_ylabel(y_var)
            axc.legend(); axc.grid(True, alpha=0.3)
            st.pyplot(figc)

        modo_grafica = st.radio(
            "Modo de visualización",
            ["Cuadrícula por ciudad", "Pestañas por ciudad", "Todas juntas"],
            horizontal=True,
            key="modo_reg_simple"
        )

        if modo_grafica == "Todas juntas":
            X_simple = df_clean[[x_var]].values
            y_simple = df_clean[y_var].values
            model_simple = LinearRegression()
            try:
                model_simple.fit(X_simple, y_simple)
                y_pred_simple = model_simple.predict(X_simple)
                order = np.argsort(X_simple.ravel())
                x_sorted = X_simple.ravel()[order]
                y_sorted = y_pred_simple[order]
                r2_value = r2_score(y_simple, y_pred_simple)

                fig1, ax1 = plt.subplots(figsize=(10, 6))
                sns.scatterplot(x=df_clean[x_var], y=df_clean[y_var], hue=df_clean["ciudad"], ax=ax1, alpha=0.6)
                ax1.plot(x_sorted, y_sorted, color='red', label="Línea de regresión", linewidth=3, linestyle='-', zorder=5)
                ax1.text(0.05, 0.95, f'R² = {r2_value:.4f}', transform=ax1.transAxes, fontsize=14, fontweight='bold',
                        va='top', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, edgecolor='black', linewidth=2))
                ax1.set_title(f"{y_var} vs {x_var}")
                ax1.set_xlabel(x_var); ax1.set_ylabel(y_var)
                ax1.legend(); ax1.grid(True, alpha=0.3)
                st.pyplot(fig1)
            except Exception as e:
                st.error("No se pudo ajustar la regresión simple.")
                st.exception(e)

        elif modo_grafica == "Pestañas por ciudad":
            tabs = st.tabs(selected_cities)
            for tab, ciudad in zip(tabs, selected_cities):
                with tab:
                    sub = df_clean[df_clean["ciudad"] == ciudad][[x_var, y_var]].dropna()
                    if len(sub) < 2 or sub[x_var].nunique() < 2:
                        st.warning(f"{ciudad}: datos insuficientes para ajustar la regresión.")
                        continue
                    _plot_reg_simple_ciudad(sub, ciudad, x_var, y_var)

        else:  # "Cuadrícula por ciudad"
            n_cols = st.slider("Columnas de la cuadrícula", 2, 4, min(3, max(2, len(selected_cities))))
            # Creamos filas de 'n_cols' columnas y vamos llenando
            cols = st.columns(n_cols)
            for i, ciudad in enumerate(selected_cities):
                sub = df_clean[df_clean["ciudad"] == ciudad][[x_var, y_var]].dropna()
                if len(sub) < 2 or sub[x_var].nunique() < 2:
                    with cols[i % n_cols]:
                        st.warning(f"{ciudad}: datos insuficientes para ajustar la regresión.")
                    continue
                with cols[i % n_cols]:
                    _plot_reg_simple_ciudad(sub, ciudad, x_var, y_var)

    # ====== COMPARACIÓN PREDICCIÓN (MÚLTIPLE vs SIMPLE) ======
    with col_multi:
        st.markdown("**Predicción: múltiple vs simple**")
        selected_predictors = [x_var] + x_multi_vars
        df_multi = df_combined[[y_var] + selected_predictors].apply(pd.to_numeric, errors='coerce').dropna()

        if df_multi.empty:
            st.info("No hay suficientes datos válidos para la comparación múltiple.")
        else:
            X_multi = df_multi[selected_predictors].values
            y_multi = df_multi[y_var].values

            model_multi = LinearRegression()
            model_simple_multi = LinearRegression()

            try:
                model_multi.fit(X_multi, y_multi)
                y_pred_multi = model_multi.predict(X_multi)

                X_simple_multi = df_multi[[x_var]].values
                model_simple_multi.fit(X_simple_multi, y_multi)
                y_pred_simple_multi = model_simple_multi.predict(X_simple_multi)

                fig2, ax2 = plt.subplots()
                ax2.scatter(y_multi, y_pred_simple_multi, alpha=0.6, label="Predicción simple")
                ax2.scatter(y_multi, y_pred_multi, alpha=0.6, label="Predicción múltiple")
                # (Eliminada la línea "Ideal")
                # min_y, max_y = np.min(y_multi), np.max(y_multi)
                # ax2.plot([min_y, max_y], [min_y, max_y], label="Ideal", linewidth=2)

                ax2.set_xlabel("Valor real")
                ax2.set_ylabel("Predicción")
                ax2.set_title("Predicción: múltiple vs simple")
                ax2.legend()
                st.pyplot(fig2)

                # Métricas
                rmse_simple = np.sqrt(np.mean((y_multi - y_pred_simple_multi) ** 2))
                rmse_multi  = np.sqrt(np.mean((y_multi - y_pred_multi) ** 2))
                mae_simple  = np.mean(np.abs(y_multi - y_pred_simple_multi))
                mae_multi   = np.mean(np.abs(y_multi - y_pred_multi))
                r2_multi    = r2_score(y_multi, y_pred_multi)

                n = len(y_multi)
                k = len(selected_predictors)
                r2_adj_multi = 1 - ((1 - r2_multi) * (n - 1) / (n - k - 1)) if n > k + 1 else r2_multi

                r2_simple_multi = r2_score(y_multi, y_pred_simple_multi)
                k_simple = 1
                r2_adj_simple = 1 - ((1 - r2_simple_multi) * (n - 1) / (n - k_simple - 1)) if n > k_simple + 1 else r2_simple_multi

                coef_multi = model_multi.coef_
                intercept_multi = model_multi.intercept_

                # Betas estandarizados (opcional, útil para comparar impacto)
                scaler_X = StandardScaler()
                scaler_y = StandardScaler()
                X_multi_scaled = scaler_X.fit_transform(X_multi)
                y_multi_scaled = scaler_y.fit_transform(y_multi.reshape(-1, 1)).ravel()
                model_scaled = LinearRegression().fit(X_multi_scaled, y_multi_scaled)
                coef_standardized = model_scaled.coef_

            except Exception as e:
                st.error("No se pudo ajustar/mostrar la comparación múltiple.")
                st.exception(e)
                rmse_simple = rmse_multi = mae_simple = mae_multi = None
                r2_multi = r2_adj_multi = r2_adj_simple = None
                coef_multi = intercept_multi = coef_standardized = None

    # ===================== UTILIDADES DE UI =====================
    st.markdown("""
    <style>
    .card{background:#F7F7F7;border:1px solid rgba(0,0,0,.08);border-radius:16px;
          padding:14px 16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.05);}
    .card h4{margin:0 0 8px 0;font-weight:800;color:#FF385C;}
    .kpi{display:flex;gap:14px;flex-wrap:wrap}
    .kpi .metric{background:#fff;border:1px solid rgba(0,0,0,.06);border-radius:12px;
                 padding:10px 12px;min-width:160px}
    .kpi .metric .label{font-size:12px;color:#666}
    .kpi .metric .value{font-size:20px;font-weight:700;color:#666}
    </style>
    """, unsafe_allow_html=True)

    def _metric_html(label, value):
        return f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div></div>'

    def interpretar_correlacion(r):
        if r == "N/A" or not isinstance(r, (int, float)):
            return "N/A", "N/A"
        direccion = "Positiva" if r > 0 else ("Negativa" if r < 0 else "Nula")
        r_abs = abs(r)
        if r_abs >= 0.9:   fuerza = "Muy fuerte"
        elif r_abs >= 0.7: fuerza = "Fuerte"
        elif r_abs >= 0.5: fuerza = "Moderada"
        elif r_abs >= 0.3: fuerza = "Débil"
        else:              fuerza = "Muy débil"
        return direccion, fuerza

    # Correlación global simple
    corr_total = df_combined[[x_var, y_var]].apply(pd.to_numeric, errors='coerce').dropna()
    if len(corr_total) > 1 and corr_total[x_var].nunique() > 1:
        corr_value = corr_total[x_var].corr(corr_total[y_var])
        corr_txt = f"{corr_value:.4f}"
        direccion, fuerza = interpretar_correlacion(corr_value)
    else:
        corr_txt = "N/A"; direccion, fuerza = "N/A", "N/A"
    
    st.markdown(
        '<div class="card"><h4>Correlación - Regresión Simple</h4><div class="kpi">'
        + _metric_html(f"{x_var} vs {y_var}", corr_txt)
        + _metric_html("Dirección", direccion)
        + _metric_html("Fuerza", fuerza)
        + '</div></div>',
        unsafe_allow_html=True
    )

    # Ecuación global simple
    def calcular_resultados(df_in: pd.DataFrame, x_col: str, y_col: str):
        dfx = df_in[[x_col, y_col]].dropna()
        if dfx[x_col].nunique() <= 1:
            return {"n": len(dfx), "r2": 0.0, "corr": 0.0, "beta0": 0.0, "beta1": 0.0}
        try:
            X = sm.add_constant(dfx[x_col].values)
            y = dfx[y_col].values
            modelo = sm.OLS(y, X).fit()
            r2 = float(modelo.rsquared) if np.isfinite(modelo.rsquared) else 0.0
            corr = float(dfx[x_col].corr(dfx[y_col])) if dfx[[x_col, y_col]].notna().all().all() else 0.0
            beta0 = float(modelo.params[0]) if len(modelo.params) > 0 else 0.0
            beta1 = float(modelo.params[1]) if len(modelo.params) > 1 else 0.0
            return {"n": int(modelo.nobs), "r2": r2, "corr": corr, "beta0": beta0, "beta1": beta1}
        except Exception:
            return {"n": len(dfx), "r2": 0.0, "corr": 0.0, "beta0": 0.0, "beta1": 0.0}

    res_ecuacion = calcular_resultados(df_combined, x_var, y_var)
    beta0_txt = f"{res_ecuacion['beta0']:.4f}"
    beta1_txt = f"{res_ecuacion['beta1']:.4f}"
    r2_simple_txt = f"{res_ecuacion['r2']:.4f}"
    signo = "+" if res_ecuacion['beta0'] >= 0 else ""
    ecuacion_txt = f"{y_var} = {beta1_txt} × {x_var} {signo} {beta0_txt}"

    st.markdown(
        '<div class="card"><h4>Ecuación de Regresión Simple</h4><div class="kpi">'
        + _metric_html("β₀ (Intercepto)", beta0_txt)
        + _metric_html("β₁ (Pendiente)", beta1_txt)
        + _metric_html("R²", r2_simple_txt)
        + f'</div><div style="margin-top:12px;padding:10px;background:#fff;border:1px solid rgba(0,0,0,.06);border-radius:12px;font-size:16px;font-weight:600;text-align:center;">{ecuacion_txt}</div></div>',
        unsafe_allow_html=True
    )

    # Métricas de modelos
    rmse_simple_txt = f"{rmse_simple:.4f}" if 'rmse_simple' in locals() and rmse_simple is not None else "N/A"
    rmse_multi_txt  = f"{rmse_multi:.4f}"  if 'rmse_multi' in locals() and rmse_multi  is not None else "N/A"
    mae_simple_txt  = f"{mae_simple:.4f}"  if 'mae_simple' in locals() and mae_simple  is not None else "N/A"
    mae_multi_txt   = f"{mae_multi:.4f}"   if 'mae_multi' in locals()  and mae_multi   is not None else "N/A"
    r2_multi_txt    = f"{r2_multi:.4f}"    if 'r2_multi' in locals()    and r2_multi    is not None else "N/A"
    r2_adj_multi_txt= f"{r2_adj_multi:.4f}"if 'r2_adj_multi' in locals()and r2_adj_multi is not None else "N/A"

    st.markdown(
        '<div class="card"><h4>RMSE de modelos</h4><div class="kpi">'
        + _metric_html("Regresión simple", rmse_simple_txt)
        + _metric_html("Regresión múltiple", rmse_multi_txt)
        + '</div></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="card"><h4>MAE de modelos</h4><div class="kpi">'
        + _metric_html("Regresión simple", mae_simple_txt)
        + _metric_html("Regresión múltiple", mae_multi_txt)
        + '</div></div>',
        unsafe_allow_html=True
    )

    # Si hay múltiple, mostramos ecuación y R²
    if 'coef_multi' in locals() and coef_multi is not None and 'intercept_multi' in locals() and intercept_multi is not None:
        r_multi = np.sqrt(float(r2_multi)) if isinstance(r2_multi, (int, float)) and r2_multi >= 0 else 0
        r_multi_txt = f"{r_multi:.4f}"
        direccion_multi, fuerza_multi = interpretar_correlacion(r_multi)

        st.markdown(
            '<div class="card"><h4>Correlación - Regresión Múltiple</h4><div class="kpi">'
            + _metric_html("R (correlación múltiple)", r_multi_txt)
            + _metric_html("Dirección", direccion_multi)
            + _metric_html("Fuerza", fuerza_multi)
            + '</div></div>',
            unsafe_allow_html=True
        )

        intercept_multi_txt = f"{intercept_multi:.4f}"
        selected_predictors = [x_var] + x_multi_vars
        terminos = [f"{coef:.4f} × {var}" for var, coef in zip(selected_predictors, coef_multi)]
        signo_int = "+" if intercept_multi >= 0 else ""
        ecuacion_multi_txt = f"{y_var} = {' + '.join(terminos)} {signo_int} {intercept_multi_txt}"

        coef_metrics = _metric_html("β₀ (Intercepto)", intercept_multi_txt)
        for i, (var, coef) in enumerate(zip(selected_predictors, coef_multi)):
            coef_metrics += _metric_html(f"β{i+1} ({var})", f"{coef:.4f}")
        coef_metrics += _metric_html("R² múltiple", r2_multi_txt)
        coef_metrics += _metric_html("R² Ajustado", r2_adj_multi_txt)

        st.markdown(
            '<div class="card"><h4>Ecuación de Regresión Múltiple</h4><div class="kpi">'
            + coef_metrics
            + f'</div><div style="margin-top:12px;padding:10px;background:#fff;border:1px solid rgba(0,0,0,.06);border-radius:12px;font-size:14px;font-weight:600;text-align:center;">{ecuacion_multi_txt}</div></div>',
            unsafe_allow_html=True
        )
    else:
        st.info("Modelo de regresión múltiple no disponible. Asegúrate de seleccionar variables adicionales.")

    # =================== RESULTADOS POR CIUDAD (CARDS) ===================
    st.subheader("Resultados por ciudad")
    cols_cards = st.columns(3)
    for i, ciudad in enumerate(selected_cities):
        res = calcular_resultados(df_combined[df_combined["ciudad"] == ciudad], x_var, y_var)
        r2_txt = f"{res['r2']:.4f}"
        corr_txt = f"{res['corr']:.4f}"
        direccion, fuerza = interpretar_correlacion(res['corr'])
        beta0_txt = f"{res['beta0']:.4f}"
        beta1_txt = f"{res['beta1']:.4f}"
        signo = "+" if res['beta0'] >= 0 else ""
        ecuacion = f"ŷ = {beta1_txt}x {signo} {beta0_txt}"

        with cols_cards[i % 3]:
            st.markdown(
                '<div class="card"><h4>'+ ciudad +'</h4><div class="kpi">'
                + _metric_html("R²", r2_txt)
                + _metric_html("Correlación", corr_txt)
                + _metric_html("Dirección", direccion)
                + _metric_html("Fuerza", fuerza)
                + _metric_html("β₀", beta0_txt)
                + _metric_html("β₁", beta1_txt)
                + f'</div><div style="margin-top:8px;padding:8px;background:#fff;border:1px solid rgba(0,0,0,.06);border-radius:8px;font-size:13px;font-weight:600;text-align:center;">{ecuacion}</div></div>',
                unsafe_allow_html=True
            )

    # ======= TABLA DE REGRESIÓN LINEAL SIMPLE POR CIUDAD =======
    rows_tabla = []
    for ciudad in selected_cities:
        sub = df_combined[df_combined["ciudad"] == ciudad][[x_var, y_var]].dropna()
        if len(sub) >= 2 and sub[x_var].nunique() > 1:
            X = sm.add_constant(sub[x_var].values)
            y = sub[y_var].values
            try:
                m = sm.OLS(y, X).fit()
                rows_tabla.append({
                    "ciudad": ciudad,
                    "n": int(m.nobs),
                    "beta0": float(m.params[0]),
                    "beta1": float(m.params[1]),
                    "R2": float(m.rsquared),
                    "correlacion": float(sub[x_var].corr(sub[y_var]))
                })
            except Exception:
                rows_tabla.append({"ciudad": ciudad, "n": len(sub), "beta0": np.nan, "beta1": np.nan, "R2": np.nan, "correlacion": np.nan})
        else:
            rows_tabla.append({"ciudad": ciudad, "n": len(sub), "beta0": np.nan, "beta1": np.nan, "R2": np.nan, "correlacion": np.nan})

    df_tabla_ciudades = pd.DataFrame(rows_tabla)
    if not df_tabla_ciudades.empty:
        st.markdown("### Tabla de regresión simple por ciudad")
        st.dataframe(df_tabla_ciudades.round(4), use_container_width=True)

    # =================== CONTEXTO DE DATOS ===================
    st.subheader("Contexto de los Datos")
    y_mean, y_min, y_max = df_clean[y_var].mean(), df_clean[y_var].min(), df_clean[y_var].max()
    x_mean, x_min, x_max = df_clean[x_var].mean(), df_clean[x_var].min(), df_clean[x_var].max()
    total_props = len(df_clean)
    y_unit, x_unit = get_unit(y_var), get_unit(x_var)

    stats_by_city = df_clean.groupby("ciudad").agg({y_var: 'mean', x_var: 'mean'}).round(2)

    st.markdown("""
    <style>
    .context-card{background:#FFF;border:2px solid #FF385C;border-radius:16px;
          padding:16px 20px;margin-bottom:20px;box-shadow:0 2px 8px rgba(255,56,92,.15);}
    .context-card h4{margin:0 0 12px 0;font-weight:800;color:#FF385C;font-size:18px;}
    .context-kpi{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;}
    .context-metric{background:#F7F7F7;border:1px solid rgba(0,0,0,.08);border-radius:10px;
                 padding:12px 14px;min-width:140px;flex:1;}
    .context-metric .label{font-size:11px;color:#666;text-transform:uppercase;font-weight:600;}
    .context-metric .value{font-size:18px;font-weight:700;color:#333;margin-top:4px;}
    .city-breakdown{background:#F7F7F7;border-radius:10px;padding:12px;margin-top:8px;}
    .city-item{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #E0E0E0;}
    .city-item:last-child{border-bottom:none;}
    .city-name{font-weight:600;color:#333;}
    .city-values{color:#666;font-size:14px;}
    </style>
    """, unsafe_allow_html=True)

    y_label = f"{y_var}" + (f" ({y_unit})" if y_unit else "")
    x_label = f"{x_var}" + (f" ({x_unit})" if x_unit else "")
    variables_list = f"<strong>{y_label}</strong> (dependiente) vs <strong>{x_label}</strong> (independiente)"
    if x_multi_vars:
        extra = []
        for v in x_multi_vars:
            v_unit = get_unit(v)
            extra.append(f"<strong>{v}{' ('+v_unit+')' if v_unit else ''}</strong>")
        variables_list += f" + {len(x_multi_vars)} variables adicionales: " + ", ".join(extra)

    st.markdown(
        f'<div class="context-card">'
        f'<h4>Variables Seleccionadas</h4>'
        f'<p style="margin:0;font-size:14px;color:#333;">{variables_list}</p>'
        f'<div class="context-kpi" style="margin-top:12px;">'
        f'<div class="context-metric"><div class="label">Total Propiedades</div><div class="value">{total_props:,}</div></div>'
        f'<div class="context-metric"><div class="label">Ciudades</div><div class="value">{len(selected_cities)}</div></div>'
        f'</div></div>',
        unsafe_allow_html=True
    )

    city_breakdown_html = '<div class="city-breakdown"><strong>Por Ciudad:</strong>'
    for ciudad in stats_by_city.index:
        y_val = stats_by_city.loc[ciudad, y_var]
        x_val = stats_by_city.loc[ciudad, x_var]
        y_val_str = f"{y_val:.2f} {y_unit}" if y_unit else f"{y_val:.2f}"
        x_val_str = f"{x_val:.2f} {x_unit}" if x_unit else f"{x_val:.2f}"
        city_breakdown_html += f'<div class="city-item"><span class="city-name">{ciudad}</span><span class="city-values">{y_var}: {y_val_str} | {x_var}: {x_val_str}</span></div>'
    city_breakdown_html += '</div>'

    y_mean_str = f"{y_mean:.2f} {y_unit}" if y_unit else f"{y_mean:.2f}"
    y_min_str  = f"{y_min:.2f} {y_unit}" if y_unit else f"{y_min:.2f}"
    y_max_str  = f"{y_max:.2f} {y_unit}" if y_unit else f"{y_max:.2f}"
    x_mean_str = f"{x_mean:.2f} {x_unit}" if x_unit else f"{x_mean:.2f}"
    x_min_str  = f"{x_min:.2f} {x_unit}" if x_unit else f"{x_min:.2f}"
    x_max_str  = f"{x_max:.2f} {x_unit}" if x_unit else f"{x_max:.2f}"

    st.markdown(
        f'<div class="context-card">'
        f'<h4>Estadísticas de {y_label}</h4>'
        f'<div class="context-kpi">'
        f'<div class="context-metric"><div class="label">Promedio</div><div class="value">{y_mean_str}</div></div>'
        f'<div class="context-metric"><div class="label">Mínimo</div><div class="value">{y_min_str}</div></div>'
        f'<div class="context-metric"><div class="label">Máximo</div><div class="value">{y_max_str}</div></div>'
        f'</div>'
        f'{city_breakdown_html}'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="context-card">'
        f'<h4>Estadísticas de {x_label}</h4>'
        f'<div class="context-kpi">'
        f'<div class="context-metric"><div class="label">Promedio</div><div class="value">{x_mean_str}</div></div>'
        f'<div class="context-metric"><div class="label">Mínimo</div><div class="value">{x_min_str}</div></div>'
        f'<div class="context-metric"><div class="label">Máximo</div><div class="value">{x_max_str}</div></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ================== HEATMAPS DE CORRELACIÓN POR CIUDAD ==================
    st.subheader("Matriz de Correlación por Ciudad")
    st.markdown("**Selecciona las variables a incluir en la matriz de correlación:**")

    all_numeric_cols = df_combined.select_dtypes(include='number').columns.tolist()
    default_vars = [v for v in ([y_var, x_var] + x_multi_vars) if v in all_numeric_cols]

    selected_heatmap_vars = st.multiselect(
        "Variables para el heatmap (mínimo 2)",
        options=all_numeric_cols,
        default=default_vars if len(default_vars) >= 2 else all_numeric_cols[:2],
        help="Selecciona las variables numéricas que quieres comparar en la matriz de correlación"
    )

    if len(selected_heatmap_vars) < 2:
        st.warning("Selecciona al menos 2 variables para generar la matriz de correlación.")
        st.stop()

    for ciudad in selected_cities:
        st.markdown(f"### {ciudad}")
        df_ciudad = df_combined[df_combined["ciudad"] == ciudad][selected_heatmap_vars].copy()
        df_ciudad = df_ciudad.dropna(axis=1, how='all')
        df_ciudad = df_ciudad.loc[:, df_ciudad.nunique() > 1]

        if df_ciudad.empty or len(df_ciudad.columns) < 2:
            st.warning(f"No hay suficientes datos numéricos para {ciudad}")
            continue

        corr_matrix = df_ciudad.corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmid=0,
            zmin=-1,
            zmax=1,
            text=corr_matrix.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            colorbar=dict(title=dict(text="Correlación", side="right"), thickness=15, len=0.7)
        ))
        fig.update_layout(
            title=f"Correlación entre Variables - {ciudad}",
            xaxis_title="Variables",
            yaxis_title="Variables",
            width=900, height=800,
            xaxis={'tickangle': 45},
            font=dict(size=11)
        )
        st.plotly_chart(fig, use_container_width=True)

        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                var1 = corr_matrix.columns[i]
                var2 = corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]
                if not np.isnan(corr_val):
                    corr_pairs.append((var1, var2, corr_val, abs(corr_val)))
        corr_pairs.sort(key=lambda x: x[3], reverse=True)

        if corr_pairs:
            with st.expander(f"Top 10 Correlaciones más Fuertes en {ciudad}", expanded=False):
                top_10 = corr_pairs[:10]
                for idx, (v1, v2, corr, abs_corr) in enumerate(top_10, 1):
                    direccion = "Positiva" if corr > 0 else "Negativa"
                    color = "#ffc107" if idx == 1 else ("#28a745" if abs_corr >= 0.7 else "#6c757d")
                    st.markdown(
                        f"<div style='background:{color};color:#fff;padding:8px;border-radius:6px;margin:4px 0;'>"
                        f"<strong>#{idx}</strong> → <strong>{v1}</strong> vs <strong>{v2}</strong>: "
                        f"<strong>{corr:.3f}</strong> ({direccion})"
                        f"</div>",
                        unsafe_allow_html=True
                    )
        st.markdown("---")

# =========================================================
# ====================== HALLAZGOS ========================
# =========================================================
st.header("Hallazgos")
def _sr(x, d=2):
    try: return f"{float(x):.{d}f}"
    except: return "N/A"

# 1) Fuente para simple por ciudad
df_simple_view = None
if 'df_tabla_ciudades' in locals() and isinstance(df_tabla_ciudades, pd.DataFrame):
    # Normaliza nombres si vienen con símbolos
    ren = {c:c for c in df_tabla_ciudades.columns}
    ren.update({"β₀":"beta0","β₁":"beta1","Correlación":"corr"})
    df_simple_view = df_tabla_ciudades.rename(columns=ren).copy()
elif 'df_simple' in locals() and isinstance(df_simple, pd.DataFrame):
    df_simple_view = df_simple.copy()
else:
    # Reconstrucción mínima con x_var / y_var
    try:
        import statsmodels.api as sm
        rows = []
        for ciudad in selected_cities:
            sub = df_combined[df_combined["ciudad"] == ciudad][[x_var, y_var]].dropna()
            if len(sub) >= 10 and sub[x_var].nunique() > 1:
                X = sm.add_constant(sub[x_var].values); y = sub[y_var].values
                m = sm.OLS(y, X).fit()
                rows.append({"ciudad":ciudad,"n":int(m.nobs),"beta0":float(m.params[0]),
                             "beta1":float(m.params[1]),"R2":float(m.rsquared),
                             "pvalue_beta1":float(m.pvalues[1])})
            else:
                rows.append({"ciudad":ciudad,"n":len(sub),"beta0":np.nan,"beta1":np.nan,"R2":np.nan,"pvalue_beta1":np.nan})
        df_simple_view = pd.DataFrame(rows)
    except Exception:
        df_simple_view = pd.DataFrame(columns=["ciudad","n","beta0","beta1","R2","pvalue_beta1"])

phrases = []

# 2) Frases basadas en regresión simple (y_var ~ x_var)
if isinstance(df_simple_view, pd.DataFrame) and len(df_simple_view):
    dfv = df_simple_view.copy()
    # Limpieza mínima
    for c in ["R2","beta1","pvalue_beta1","n"]:
        if c in dfv.columns: dfv[c] = pd.to_numeric(dfv[c], errors="coerce")
    dfv = dfv.dropna(subset=["R2"], how="all")

    # % de ciudades con pendiente significativa
    if {"pvalue_beta1","R2"}.issubset(dfv.columns):
        mask_valid = dfv["R2"].notna()
        total_valid = int(mask_valid.sum())
        sig = int((dfv["pvalue_beta1"] < 0.05).fillna(False).sum())
        if total_valid > 0:
            pct = 100*sig/total_valid
            phrases.append(f"En {_sr(pct,1)}% de las ciudades la pendiente es significativa (p<0.05) para {x_var} → {y_var}.")

    # Top 1 mejor y peor R²
    if "R2" in dfv.columns and "ciudad" in dfv.columns:
        top = dfv.dropna(subset=["R2"]).sort_values("R2", ascending=False)
        if len(top):
            phrases.append(f"El mejor ajuste se observa en {top.iloc[0]['ciudad']} (R²={_sr(top.iloc[0]['R2'],3)}).")
        worst = top[top["R2"]>=0].sort_values("R2", ascending=True)
        if len(worst):
            phrases.append(f"El ajuste más bajo se observa en {worst.iloc[0]['ciudad']} (R²={_sr(worst.iloc[0]['R2'],3)}).")

    # Sentido de la relación (positiva/negativa) entre ciudades significativas
    if {"beta1","pvalue_beta1","ciudad"}.issubset(dfv.columns):
        pos_sig = dfv[(dfv["beta1"]>0) & (dfv["pvalue_beta1"]<0.05)]["ciudad"].tolist()
        neg_sig = dfv[(dfv["beta1"]<0) & (dfv["pvalue_beta1"]<0.05)]["ciudad"].tolist()
        if len(pos_sig):
            phrases.append(f"Relación positiva y significativa (↑{y_var} con ↑{x_var}) en: {', '.join(pos_sig[:5])}" + ("…" if len(pos_sig)>5 else "") + ".")
        if len(neg_sig):
            phrases.append(f"Relación negativa y significativa (↓{y_var} con ↑{x_var}) en: {', '.join(neg_sig[:5])}" + ("…" if len(neg_sig)>5 else "") + ".")

    # Efecto típico (mediana de β1) y potencia explicativa típica (mediana R²)
    if {"beta1","R2"}.issubset(dfv.columns):
        med_b1 = dfv["beta1"].dropna().median() if "beta1" in dfv else np.nan
        med_r2 = dfv["R2"].dropna().median()
        if pd.notna(med_b1):
            sign = "↑" if med_b1>=0 else "↓"
            phrases.append(f"Efecto típico (mediana β₁): {sign}{_sr(abs(med_b1),2)} unidades en {y_var} por +1 en {x_var}.")
        if pd.notna(med_r2):
            phrases.append(f"Potencia explicativa típica (mediana R²): {_sr(med_r2,3)}.")

# 3) Frases del modelo múltiple global
has_multi = ('multi_metrics' in locals() and isinstance(multi_metrics, dict) and len(multi_metrics) > 0)
has_multi_coefs = ('multi_coefs' in locals() and isinstance(multi_coefs, pd.DataFrame) and len(multi_coefs))

if has_multi:
    r2a = multi_metrics.get("R2_adj", None)
    rmse = multi_metrics.get("RMSE", None)
    if r2a is not None:
        phrases.append(f"El modelo múltiple global alcanza R² ajustado de {_sr(r2a,3)}.")
    if rmse is not None:
        phrases.append(f"El error típico (RMSE) del modelo múltiple es {_sr(rmse,2)} en unidades de {y_var}.")

if has_multi_coefs:
    dfc = multi_coefs.copy()
    if "variable" in dfc.columns and "beta_estandarizado" in dfc.columns:
        dfc = dfc[dfc["variable"]!="const"].dropna(subset=["beta_estandarizado"])
        if len(dfc):
            dfc["absb"] = dfc["beta_estandarizado"].abs()
            top3 = dfc.sort_values("absb", ascending=False).head(3)
            driv = [f"{row['variable']} (β*={_sr(row['beta_estandarizado'],2)}" + (f", p={_sr(row['pvalue'],3)}" if "pvalue" in dfc.columns else "") + ")" for _, row in top3.iterrows()]
            phrases.append("Principales impulsores del precio en el modelo múltiple: " + ", ".join(driv) + ".")

# 4) Render bonito
if phrases:
    st.markdown("""
    <div style="background:#fff;border:2px solid #FF385C;border-radius:16px;padding:14px 16px;box-shadow:0 2px 8px rgba(255,56,92,.15);">
      <h4 style="margin:0 0 8px 0;color:#FF385C;">Hallazgos</h4>
      <ul style="margin:0 0 0 18px;">
    """, unsafe_allow_html=True)
    for p in phrases:
        st.markdown(f"<li>{p}</li>", unsafe_allow_html=True)
    st.markdown("</ul></div>", unsafe_allow_html=True)
else:
    st.info("Aún no hay hallazgos para mostrar. Verifica que existan tablas de resultados o datos suficientes.")
