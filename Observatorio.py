from datetime import date, timedelta

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# Definir variables y constantes

TOKEN = st.secrets["X_APP_TOKEN"]

URL = "https://www.datos.gov.co/resource/p6dx-8zbt.json"
URL_ENTIDADES = "https://www.datos.gov.co/resource/h7zv-k39x.json"
URL_PAA = "https://www.datos.gov.co/resource/b6m4-qgqv.json"

COLS_ENTIDADES = ["NOMBRE", "CCB_NIT_INST", "ORDEN", "SECTOR"]

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

OFFSET = 1000

HOY = date.today()
ayer = HOY - timedelta(days=7)


# Definir funciones


@st.cache_resource(show_spinner="Cargando modelo para similitud semántica...")
def load_embedder(model_id):
    return SentenceTransformer(model_id)


@st.cache_data(show_spinner="Calculando vectores...")
def encode_texts(_embedder, texts):
    embeddings = _embedder.encode(texts, convert_to_tensor=True)

    return embeddings


@st.cache_resource
def create_session(token):
    session = requests.Session()
    session.headers.update({"X-App-token": token})

    return session


@st.cache_data(show_spinner="Buscando en Socrata API...")
def buscar_socrata(_session, url, payload):
    n = OFFSET + 0

    r = _session.get(url, params=payload)

    if r.status_code in [200, 202]:
        procesos = r.json()
        params = payload.copy()

        while len(procesos) == n:
            params.update({"$offset": n})

            r = _session.get(url, params=params)
            if r.status_code in [200, 202]:
                procesos.extend(r.json())
                n += OFFSET

            else:
                break
    else:
        procesos = []

    return procesos


@st.cache_data(show_spinner="Cargando entidades del Estado...")
def crear_df_entidades():
    df_entidades = pd.read_csv(
        "data/entidades.csv",
        encoding="utf-8",
        dtype={"CCB_NIT_INST": str},
        usecols=COLS_ENTIDADES,
    )

    return df_entidades


@st.cache_data(show_spinner="Creando tabla de procesos...")
def crear_df_procesos(procesos):
    df_procesos = pd.DataFrame.from_records(procesos)
    df_procesos = df_procesos.dropna(subset=["descripci_n_del_procedimiento"])
    df_procesos = df_procesos.drop_duplicates(subset=["id_del_proceso", "entidad"])
    df_procesos = df_procesos.reset_index(drop=True)

    return df_procesos


def payload_procesos(
    fechas,
    precio_minimo=0,
    orden=None,
    entidades=None,
    fases=None,
    modalidades=None,
):
    # https://dev.socrata.com/foundry/www.datos.gov.co/p6dx-8zbt
    if isinstance(fechas, tuple):
        inicio, fin = fechas
    else:
        inicio = fechas
        fin = HOY

    inicial = f'{inicio.strftime("%Y-%m-%d")}T00:00:00'
    final = f'{fin.strftime("%Y-%m-%d")}T23:59:59'

    where_query = f"fecha_de_publicacion_del between '{inicial}' and '{final}'"

    if precio_minimo > 0:
        where_query = f"{where_query} AND precio_base > {precio_minimo}"

    if entidades is not None:
        where_query = f"{where_query} AND entidad in{tuple(e for e in entidades)}"

    if fases is not None:
        where_query = f"{where_query} AND fase in{tuple(f for f in fases)}"

    if modalidades is not None:
        where_query = f"{where_query} AND modalidad_de_contratacion in{tuple(m for m in modalidades)}"

    payload = {
        "$where": where_query,
        "$order": "fecha_de_publicacion_del DESC",
        "$limit": OFFSET,
    }

    if orden is not None:
        payload.update({"ordenentidad": orden})

    return payload


def payload_entidades(nits=None):
    # https://dev.socrata.com/foundry/www.datos.gov.co/h7zv-k39x

    payload = {"$limit": OFFSET}
    where_query = ""

    if nits is not None:
        if isinstance(nits, list):
            nits = set(nits)
        where_query = f"ccb_nit_inst in{tuple(e for e in nits)}"

    if where_query:
        payload.update({"$where": where_query})

    return payload


def payload_paa(anno=None):
    # https://dev.socrata.com/foundry/www.datos.gov.co/b6m4-qgqv

    payload = {"$limit": OFFSET}
    where_query = ""

    if anno is not None:
        where_query = f"anno = {anno}"

    if where_query:
        payload.update({"$where": where_query})

    return payload


def normalizar_textual(df, col):
    normalizada = (
        df[col]
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )

    return normalizada


# Preparar ui

st.set_page_config(page_title="Observatorio de Mercado", page_icon="👋", layout="wide")

st.title(":flag-co: Observatorio de mercado de contratación pública")

st.sidebar.success("Seleccione alguna de las pestañas disponibles.")

st.markdown(
    """Aplicaciones para el estudio de la contratación pública. **👈 Seleccione alguna pestaña de la izquierda** para diferentes análisis.
    """
)

st.markdown("---")


# Aca se modifica todo
