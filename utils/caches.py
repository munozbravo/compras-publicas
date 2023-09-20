from pathlib import Path

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


@st.cache_data(show_spinner="Cargando archivo requerido...")
def cargar_df(fp, tipos=None, columnas=None, ordenar=None, ascending=True):
    ruta = Path(fp)

    if ruta.suffix == ".csv":
        df = pd.read_csv(ruta, encoding="utf-8", dtype=tipos, usecols=columnas)
    elif ruta.suffix == ".xlsx":
        df = pd.read_excel(ruta, dtype=tipos, usecols=columnas)

    if ordenar is not None:
        df = df.sort_values(by=ordenar, ascending=ascending)

    return df
