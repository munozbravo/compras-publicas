from datetime import date, timedelta

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from sentence_transformers import util
import pandas as pd
import streamlit as st

from utils.caches import configurar_pagina

from utils.caches import (
    load_embedder,
    encode_texts,
    create_session,
    buscar_socrata,
    crear_df_resultados,
)
from utils.variables import URL_PROCESOS, URL_ENTIDADES_FP, COLS_PROCESOS, ORDEN_ENTIDAD


configurar_pagina(title="Procesos de contratación pública", icon="📈", layout="wide")


# Definir funciones


def payload_procesos(
    fechas,
    precio_minimo=0,
    offset=1000,
    orden=None,
    entidades=None,
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

    if orden is not None:
        where_query = f"{where_query} AND ordenentidad = '{orden}'"

    if entidades is not None:
        where_query = f"{where_query} AND entidad in{tuple(e for e in entidades)}"

    payload = {
        "$where": where_query,
        "$order": "fecha_de_publicacion_del DESC",
        "$limit": offset,
    }

    return payload


def payload_entidades(offset=1000, selection=None, select_col=None, sort=None):
    # https://dev.socrata.com/foundry/www.datos.gov.co/h7zv-k39x
    # https://dev.socrata.com/foundry/www.datos.gov.co/pajg-ux27

    payload = {"$limit": offset}

    if sort is not None:
        payload.update({"$order": sort})

    where_query = ""

    if (selection is not None) and (select_col is not None):
        if isinstance(selection, list):
            selection = set(selection)
        where_query = f"{select_col} in{tuple(e for e in selection)}"

    if where_query:
        payload.update({"$where": where_query})

    return payload


def limpiar_resultados():
    st.session_state.seleccion = None


# Definir variables y constantes

TOKEN = st.secrets["X_APP_TOKEN"]

COLS_NA = ["descripci_n_del_procedimiento"]
COLS_DUP = ["id_del_proceso", "entidad"]

COLS_ENTIDADES = ["nombre", "ccb_nit_inst", "orden", "sector", "naturaleza_juridica"]

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

OFFSET = 1000

HOY = date.today()
ayer = HOY - timedelta(days=7)

session = create_session(TOKEN)

if "procesos" not in st.session_state:
    st.session_state.procesos = []

if "seleccion" not in st.session_state:
    st.session_state.seleccion = {}

# Preparar ui


st.title(":flag-co: Búsqueda en procesos de contratación")

st.markdown(
    """Aplicación para encontrar similitud semántica en descripción de procesos de contratación."""
)

st.markdown("---")


with st.sidebar:
    fechas = st.date_input("Rango de fechas", [ayer, HOY], max_value=HOY)

    precio_minimo = st.number_input(
        "Monto mínimo", 0, value=50000000, step=10000000, format="%d"
    )

    orden_entidad = st.selectbox("Tipo de entidad", ORDEN_ENTIDAD)

    boton = st.button("Buscar procesos", on_click=limpiar_resultados)


# Aca se modifica todo

embedder = load_embedder(MODELO)

with st.spinner("Cargando listado de sectores..."):
    pay_ents = payload_entidades(offset=OFFSET, sort="nombre ASC")
    ents = buscar_socrata(
        _session=session, url=URL_ENTIDADES_FP, payload=pay_ents, offset=OFFSET
    )

    df_ents = crear_df_resultados(ents, na_cols=["nombre"])
    df_ents = df_ents[COLS_ENTIDADES]

if boton:
    payload = payload_procesos(
        fechas,
        precio_minimo=precio_minimo,
        offset=OFFSET,
        orden=orden_entidad,
    )

    procesos = buscar_socrata(
        _session=session, url=URL_PROCESOS, payload=payload, offset=OFFSET
    )

    st.session_state.procesos = [
        {k: proceso.get(k) for k in proceso.keys() if k in COLS_PROCESOS}
        for proceso in procesos
    ]

    if st.session_state.procesos:
        n = len(st.session_state.procesos)
        inicio, fin = fechas
        st.info(
            f'Búsqueda entre {inicio.strftime("%Y-%m-%d")} y {fin.strftime("%Y-%m-%d")}. Valor mínimo ${precio_minimo:,.0f}. Entidades de orden {orden_entidad}.',
            icon="ℹ️",
        )
        st.info(f"{n} registros encontrados.", icon="🔥")


if st.session_state.procesos:
    df_procesos = crear_df_resultados(
        st.session_state.procesos, na_cols=COLS_NA, dup_cols=COLS_DUP
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
                df_ents, how="left", left_on="nit_entidad", right_on="ccb_nit_inst"
            )

            COLS = COLS_PROCESOS + ["sector", "score"]

            df_similarity = df_similarity[COLS]
            df_similarity = df_similarity.reset_index(drop=True)

            st.session_state.seleccion = df_similarity.to_dict()

if st.session_state.seleccion:
    df_similarity = pd.DataFrame.from_dict(st.session_state.seleccion)
    gb = GridOptionsBuilder.from_dataframe(df_similarity)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gridOptions = gb.build()

    grid = AgGrid(
        df_similarity,
        gridOptions,
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

                    Sector: :blue[{fila.get('sector')}]
                    
                    Modalidad: {fila.get('modalidad_de_contratacion')}

                    Adjudicado: :{color_adjud}[{adjudicado}]

                    [URL del proceso]({fila.get('urlproceso')})
                """
            )

            if adjudicado == "Si":
                st.markdown(f"Proveedor: {fila.get('nombre_del_proveedor')}")

            st.divider()
