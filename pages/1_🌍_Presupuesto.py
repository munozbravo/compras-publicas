from pathlib import Path

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# Definir variables y constantes

TOKEN = st.secrets["X_APP_TOKEN"]

URL_ENTIDADES = "https://www.datos.gov.co/resource/h7zv-k39x.json"
URL_PAA = "https://www.datos.gov.co/resource/b6m4-qgqv.json"

COLS_ENTIDADES = ["NOMBRE", "CCB_NIT_INST", "ORDEN", "SECTOR"]

OFFSET = 1000


# Definir funciones


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

st.set_page_config(
    page_title="Presupuesto de entidades estatales", page_icon="🌍", layout="wide"
)

st.title(":flag-co: Presupuesto de entidades estatales")

st.markdown("""Aplicación para dimensionar el presupuesto de entidades por sector.""")

st.markdown("---")


# Aca se modifica todo

df_entidades = crear_df_entidades()

session = create_session(TOKEN)

prep_ppa = payload_paa(2023)
paas = buscar_socrata(_session=session, url=URL_PAA, payload=prep_ppa)

df_paa = pd.DataFrame.from_records(paas)
df_paa["valor_presupuesto_general"] = pd.to_numeric(df_paa["valor_presupuesto_general"])

df_paa["normalizado"] = normalizar_textual(df_paa, "nombre_entidad")
df_entidades["normalizado"] = normalizar_textual(df_entidades, "NOMBRE")


df_paa = df_paa.merge(
    df_entidades, how="left", left_on="normalizado", right_on="normalizado"
)

df_paa[COLS_ENTIDADES] = df_paa[COLS_ENTIDADES].fillna("No identificado")

fig = px.treemap(
    df_paa,
    path=[px.Constant("Todos"), "ORDEN", "SECTOR", "NOMBRE"],
    values="valor_presupuesto_general",
    color="SECTOR",
)

fig.update_traces(
    root_color="lightgrey",
    hovertemplate="<b>%{label}</b><br><b>Monto</b> %{value:,.2f}",
    texttemplate="<b>%{label}</b><br><b>Monto</b> %{value:,.2f}",
    textinfo="label+value",
)

st.plotly_chart(fig, use_container_width=True)
