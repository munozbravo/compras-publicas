from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from sentence_transformers import util
import pandas as pd
import plotly.express as px
import streamlit as st

from data.rutas import ENTIDADES, META_PAA, DIR_PAA
from utils.caches import cargar_df, load_embedder, encode_texts
from utils.config import configurar_pagina
from utils.variables import COLS_ENTIDADES, COLS_PAA


configurar_pagina("Planes anuales de adquisición", "💸", "wide")


# Definir variables y constantes

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

RENOMBRES = {
    "Código UNSPSC (cada código separado por ;)": "unspsc",
    "Descripción": "descripcion",
    "Fecha estimada de inicio de proceso de selección (mes)": "mes_inicio",
    "Fecha estimada de presentación de ofertas (mes)": "mes_oferta",
    "Duración del contrato (número)": "duracion",
    "Duración del contrato (intervalo: días, meses, años)": "intervalo",
    "Modalidad de selección ": "modalidad",
    "Fuente de los recursos": "fuente",
    "Valor total estimado": "valor",
    "Valor estimado en la vigencia actual": "valor_vigencia",
    "¿Se requieren vigencias futuras?": "vigencias_futuras",
    "Estado de solicitud de vigencias futuras": "solicitud_vigencias",
    "Unidad de contratación (referencia)": "unidad",
    "Ubicación": "ubicacion",
    "Nombre del responsable ": "responsable",
    "Teléfono del responsable ": "telefono",
    "Correo electrónico del responsable ": "email",
    "¿Debe cumplir con invertir mínimo el 30% de los recursos del presupuesto destinados a comprar alimentos, cumpliendo con lo establecido en la Ley 2046 de 2020, reglamentada por el Decreto 248 de 2021?": "otra1",
    "¿El contrato incluye el suministro de bienes y servicios distintos a alimentos?": "otra2",
}


# Datos globales y config

df_meta = cargar_df(META_PAA, {"nit_entidad": str}, ordenar="entidad")


# Preparar ui

st.title(":flag-co: Búsqueda en Planes Anuales de Adquisición")

st.markdown(
    """Búsqueda semántica en la descripción de Planes Anuales de Adquisición."""
)

st.markdown("---")

opt_entidades = st.multiselect("Seleccione entidades", df_meta["entidad"])

query = st.text_input("Consulta a realizar")


# Aca se modifica todo

embedder = load_embedder(MODELO)

df_entidades = cargar_df(
    ENTIDADES, tipos={"CCB_NIT_INST": str}, columnas=COLS_ENTIDADES
)

if opt_entidades and query:
    df_filtrado = df_meta[df_meta["entidad"].isin(opt_entidades)]

    dfs = []

    for row in df_filtrado.itertuples():
        df = pd.read_excel(DIR_PAA.joinpath(row.archivo), skiprows=1)
        df.rename(RENOMBRES, inplace=True, axis=1)
        df = df[COLS_PAA]
        df["entidad"] = row.entidad
        df["nit_entidad"] = row.nit_entidad
        dfs.append(df)

    df_paa = pd.concat(dfs, ignore_index=True)

    corpus = df_paa["descripcion"].to_list()

    if corpus:
        corpus_embeddings = encode_texts(embedder, corpus)

    if query:
        query_embedding = encode_texts(embedder, query)

    if corpus and query:
        hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=10)

        query_hits = hits[0]

        ids = [hit["corpus_id"] for hit in query_hits]

        df_similarity = df_paa.loc[ids]
        df_similarity["score"] = [hit["score"] for hit in query_hits]

        df_similarity["nit_entidad"] = df_similarity["nit_entidad"].astype(str)

        df_similarity = df_similarity.merge(
            df_entidades, how="left", left_on="nit_entidad", right_on="CCB_NIT_INST"
        )

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
            if len(selected_rows) > 2:
                cols = ["ORDEN", "SECTOR", "entidad", "valor"]
                seleccion = pd.DataFrame(selected_rows)[cols]

                seleccion["valor"] = pd.to_numeric(seleccion["valor"])

                seleccion = seleccion.map(lambda x: x if x else "No Identificado")

                seleccion = seleccion.dropna(thresh=2)

                fig = px.treemap(
                    seleccion,
                    path=[px.Constant("Todos"), "ORDEN", "SECTOR", "entidad"],
                    values="valor",
                    color="SECTOR",
                )

                fig.update_traces(
                    root_color="lightgrey",
                    hovertemplate="<b>%{label}</b><br><b>Monto</b> %{value:,.2f}",
                    texttemplate="<b>%{label}</b><br><b>Monto</b> %{value:,.2f}",
                    textinfo="label+value",
                )

                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            for fila in selected_rows:
                score = fila.get("score")
                color_score = "green" if score > 0.6 else "red"

                st.markdown(
                    f"""
                        ## Descripción
                        {fila.get('descripcion')}

                        Entidad: :blue[{fila.get('entidad')}]

                        Duración: {fila.get('duracion')} {fila.get('intervalo')}

                        Valor: :blue[{float(fila.get('valor')):,.2f}]

                        Inicio proceso: {fila.get('mes_inicio')}

                        Sector: :blue[{fila.get('SECTOR')}]
                        
                        Modalidad: {fila.get('modalidad')}

                        Score
                        :{color_score}[{fila.get('score'):.2f}]
                    """
                )
