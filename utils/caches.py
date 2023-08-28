from sentence_transformers import SentenceTransformer
import pandas as pd
import requests
import streamlit as st


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
def buscar_socrata(_session, url, payload, offset=1000):
    n = offset + 0

    r = _session.get(url, params=payload)

    if r.status_code in [200, 202]:
        resultados = r.json()
        params = payload.copy()

        while len(resultados) == n:
            params.update({"$offset": n})

            r = _session.get(url, params=params)
            if r.status_code in [200, 202]:
                resultados.extend(r.json())
                n += offset

            else:
                break
    else:
        resultados = []

    return resultados


@st.cache_data(show_spinner="Creando tabla de resultados...")
def crear_df_resultados(resultados, na_cols=None, dup_cols=None):
    df = pd.DataFrame.from_records(resultados)

    if na_cols is not None:
        df = df.dropna(subset=na_cols)
    if dup_cols is not None:
        df = df.drop_duplicates(subset=dup_cols)

    if (na_cols is not None) or (dup_cols is not None):
        df = df.reset_index(drop=True)

    return df


def configurar_pagina(title: str, icon: str, layout: str = "wide"):
    """Iniciar configuracion de página.

    Parameters
    ----------
    title : str
        Nombre de la página
    icon : str
        Icono de la página
    layout : str
        Layout inicial de la página
    """

    return st.set_page_config(page_title=title, page_icon=icon, layout=layout)
