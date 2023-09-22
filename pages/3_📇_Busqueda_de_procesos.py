from datetime import date, timedelta

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from sentence_transformers import util
import pandas as pd
import streamlit as st

from data.rutas import ENTIDADES
from utils.caches import (
    load_embedder,
    encode_texts,
    create_session,
    buscar_socrata,
    crear_df_resultados,
    cargar_df,
    limpiar_estado,
)
from utils.config import configurar_pagina
from utils.helpers import validar_fechas
from utils.socrata import payload_procesos
from utils.variables import URL_PROCESOS, COLS_PROCESOS, ORDEN_ENTIDAD


configurar_pagina(title="Procesos de contratación pública", icon="📇", layout="wide")


# Definir variables y constantes

TOKEN = st.secrets["X_APP_TOKEN"]

COLS_NA = ["descripci_n_del_procedimiento"]
COLS_DUP = ["id_del_proceso", "entidad"]

COLS_ENTIDADES = ["NOMBRE", "CCB_NIT_INST", "ORDEN", "SECTOR"]

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

OFFSET = 1000

HOY = date.today()
ayer = HOY - timedelta(days=14)

session = create_session(TOKEN)

k1 = "procesos"
k2 = "seleccion"

if k1 not in st.session_state:
    st.session_state[k1] = []

if k2 not in st.session_state:
    st.session_state[k2] = {}

# Preparar ui


st.title(":flag-co: Búsqueda en procesos de contratación")

st.markdown("""Búsqueda semántica en la descripción de procesos de contratación.""")

st.markdown("---")


with st.sidebar:
    fechas = st.date_input("Rango de fechas", [ayer, HOY], max_value=HOY)

    precio_minimo = st.number_input(
        "Monto mínimo", 0, value=50000000, step=10000000, format="%d"
    )

    orden_entidad = st.selectbox("Tipo de entidad", ORDEN_ENTIDAD)

    boton = st.button("Buscar procesos", on_click=limpiar_estado, args=(k2,))


# Aca se modifica todo

embedder = load_embedder(MODELO)

with st.spinner("Cargando listado de sectores..."):
    df_ents = cargar_df(ENTIDADES, {"CCB_NIT_INST": str}, COLS_ENTIDADES)

if boton:
    inicio, fin = validar_fechas(fechas)

    payload = payload_procesos(
        fechas=(inicio, fin),
        precio_minimo=precio_minimo,
        offset=OFFSET,
        orden=orden_entidad,
        sort="fecha_de_publicacion_del DESC",
    )

    procesos = buscar_socrata(
        _session=session, url=URL_PROCESOS, payload=payload, offset=OFFSET
    )

    st.session_state[k1] = [
        {k: proceso.get(k) for k in proceso.keys() if k in COLS_PROCESOS}
        for proceso in procesos
    ]

    n = len(st.session_state[k1])

    st.info(
        f'Búsqueda entre {inicio.strftime("%Y-%m-%d")} y {fin.strftime("%Y-%m-%d")}. Valor mínimo ${precio_minimo:,.0f}. Entidades de orden {orden_entidad}.',
        icon="ℹ️",
    )
    st.info(f"{n} registros encontrados.", icon="🔥")


if st.session_state[k1]:
    df_procesos = crear_df_resultados(
        st.session_state[k1], na_cols=COLS_NA, dup_cols=COLS_DUP
    )

    df_procesos["urlproceso"] = df_procesos["urlproceso"].apply(lambda x: x.get("url"))

    entidades = list(df_procesos["entidad"].sort_values().unique())
    sel_entidades = st.multiselect("Entidades a considerar (opcional)", entidades)

    if sel_entidades:
        df_procesos = df_procesos[df_procesos["entidad"].isin(sel_entidades)]
        df_procesos = df_procesos.reset_index(drop=True)

    corpus = df_procesos["descripci_n_del_procedimiento"].to_list()

    query = st.text_input("Consulta a realizar")

    btn_filtro = st.button("Filtrar resultados")

    if btn_filtro:
        corpus_embeddings = encode_texts(embedder, corpus)

        if query:
            query_embedding = encode_texts(embedder, query)

            hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=10)

            query_hits = hits[0]

            ids = [hit["corpus_id"] for hit in query_hits]

            df_similarity = df_procesos.loc[ids]
            df_similarity["score"] = [hit["score"] for hit in query_hits]

            df_similarity = df_similarity.merge(
                df_ents, how="left", left_on="nit_entidad", right_on="CCB_NIT_INST"
            )

            COLS = COLS_PROCESOS + ["SECTOR", "score"]

            df_similarity = df_similarity[COLS]
            df_similarity = df_similarity.reset_index(drop=True)

            st.session_state[k2] = df_similarity.to_dict()

if st.session_state[k2]:
    df_similarity = pd.DataFrame.from_dict(st.session_state[k2])
    gb = GridOptionsBuilder.from_dataframe(df_similarity)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gridOptions = gb.build()

    grid = AgGrid(
        df_similarity,
        gridOptions,
        height=250,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
    )

    selected_rows = grid["selected_rows"]

    if len(selected_rows) >= 1:
        for fila in selected_rows:
            score = fila.get("score")
            color_score = "green" if score > 0.6 else "red"

            adjudicado = fila.get("adjudicado")
            color_adjud = "green" if adjudicado == "Si" else "red"

            st.markdown(
                f"""
                    ## Descripción
                    {fila.get('descripci_n_del_procedimiento')}

                    Score: :{color_score}[{score:.2f}]

                    Entidad: :blue[{fila.get('entidad')}]

                    Valor: :blue[{float(fila.get('precio_base')):,.2f}]

                    Duración: {fila.get('duracion')} {fila.get('unidad_de_duracion')}

                    Publicado: {fila.get('fecha_de_publicacion_del')}

                    Sector: :blue[{fila.get('SECTOR')}]
                    
                    Modalidad: {fila.get('modalidad_de_contratacion')}

                    Adjudicado: :{color_adjud}[{adjudicado}]

                    [URL del proceso]({fila.get('urlproceso')})
                """
            )

            if adjudicado == "Si":
                st.markdown(f"Proveedor: {fila.get('nombre_del_proveedor')}")

            st.divider()
