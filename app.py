from datetime import date, timedelta
import json
import os

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from sentence_transformers import SentenceTransformer, util
import numpy as np
import pandas as pd
import requests
import streamlit as st


# Definir variables y constantes

TOKEN = st.secrets["X_APP_TOKEN"]
URL = "https://www.datos.gov.co/resource/p6dx-8zbt.json"

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


@st.cache_data(show_spinner="Buscando procesos de contratación...")
def buscar_procesos(_session, payload):
    n = OFFSET + 0

    r = _session.get(URL, params=payload)

    if r.status_code in [200, 202]:
        procesos = r.json()
        params = payload.copy()

        while len(procesos) == n:
            params.update({"$offset": n})

            r = _session.get(URL, params=params)
            if r.status_code in [200, 202]:
                procesos.extend(r.json())
                n += OFFSET

            else:
                break
    else:
        procesos = []

    return procesos


@st.cache_data(show_spinner="Creando tabla de procesos...")
def crear_df_procesos(procesos):
    df_procesos = pd.DataFrame.from_records(procesos)
    df_procesos.dropna(subset=["descripci_n_del_procedimiento"], inplace=True)
    df_procesos.drop_duplicates(subset=["id_del_proceso", "entidad"], inplace=True)
    df_procesos.reset_index(drop=True, inplace=True)

    return df_procesos


def preparar_consulta_socrata(
    fechas,
    precio_minimo=0,
    orden="Nacional",
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
        "ordenentidad": orden,
        "$order": "fecha_de_publicacion_del DESC",
        "$limit": OFFSET,
    }

    return payload


# Preparar ui


st.title(":flag-co: Búsqueda en procesos de contratación pública")

st.markdown(
    """Aplicación para encontrar similitud semántica en descripción de procesos de contratación."""
)

st.markdown("---")


with st.sidebar:
    fechas = st.date_input("Rango de fechas", [ayer, HOY], max_value=HOY)

    precio_minimo = 50000000

    boton = st.button("Buscar procesos")

query = st.text_input("Consulta a realizar")
# btn_query = st.button("Calcular similitud")


if "procesos" not in st.session_state:
    st.session_state.procesos = []


# Aca se modifica todo

embedder = load_embedder(MODELO)

session = create_session(TOKEN)

if boton:
    payload = preparar_consulta_socrata(fechas, 50000000)

    procesos = buscar_procesos(_session=session, payload=payload)
    st.session_state.procesos = procesos


if query:
    query_embedding = encode_texts(embedder, query)

    if st.session_state.procesos:
        df_procesos = crear_df_procesos(st.session_state.procesos)
        corpus = df_procesos["descripci_n_del_procedimiento"].to_list()
        corpus_embeddings = encode_texts(embedder, corpus)

        hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=10)

        query_hits = hits[0]

        ids = [hit["corpus_id"] for hit in query_hits]

        df_similarity = df_procesos.loc[ids]
        df_similarity["score"] = [hit["score"] for hit in query_hits]

        COLS = [
            "id_del_proceso",
            "entidad",
            "precio_base",
            "fecha_de_publicacion_del",
            "descripci_n_del_procedimiento",
            "duracion",
            "unidad_de_duracion",
            "modalidad_de_contratacion",
            "score",
        ]

        df_similarity = df_similarity[COLS]
        df_similarity.reset_index(drop=True, inplace=True)

        gb = GridOptionsBuilder.from_dataframe(df_similarity)
        gb.configure_selection(selection_mode="single", use_checkbox=True)
        gridOptions = gb.build()
        prueba = AgGrid(
            df_similarity,
            gridOptions,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
        )

        selected_rows = prueba["selected_rows"]

        if len(selected_rows) == 1:
            fila = selected_rows[0]

            st.divider()

            st.markdown(
                f"""
                    ## Descripción
                    {fila.get('descripci_n_del_procedimiento')}

                    Entidad: {fila.get('entidad')}

                    Duración: {fila.get('duracion')} {fila.get('unidad_de_duracion')}

                    Valor: {float(fila.get('precio_base')):,.2f}

                    Publicado: {fila.get('fecha_de_publicacion_del')}

                    Modalidad: {fila.get('modalidad_de_contratacion')}

                    Score
                    :red[{fila.get('score'):.2f}]
                """
            )
