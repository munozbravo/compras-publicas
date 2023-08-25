from pathlib import Path

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import plotly.express as px
import streamlit as st


# Definir variables y constantes

COLS_ENTIDADES = ["NOMBRE", "CCB_NIT_INST", "ORDEN", "SECTOR"]

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


COLS_PLANES = [
    "unspsc",
    "descripcion",
    "mes_inicio",
    "mes_oferta",
    "duracion",
    "intervalo",
    "modalidad",
    "fuente",
    "valor",
    "unidad",
    "ubicacion",
]

dir_data = Path("data")


# Definir funciones


@st.cache_resource(show_spinner="Cargando modelo para similitud semántica...")
def load_embedder(model_id):
    return SentenceTransformer(model_id)


@st.cache_data(show_spinner="Calculando vectores...")
def encode_texts(_embedder, texts):
    embeddings = _embedder.encode(texts, convert_to_tensor=True)

    return embeddings


@st.cache_data(show_spinner="Cargando entidades del Estado...")
def crear_df_entidades():
    df_entidades = pd.read_csv(
        dir_data.joinpath("entidades.csv"),
        encoding="utf-8",
        dtype={"CCB_NIT_INST": str},
        usecols=COLS_ENTIDADES,
    )

    return df_entidades


@st.cache_data(show_spinner="Cargando metadata Planes Anuales de Adquisición...")
def crear_df_metadata():
    df_meta = pd.read_excel(dir_data.joinpath("paa.xlsx"), dtype={"nit_entidad": str})

    df_meta = df_meta.sort_values(by="entidad")

    return df_meta


# Datos globales y config


st.set_page_config(
    page_title="Planes anuales de adquisición", page_icon="📊", layout="wide"
)

df_meta = crear_df_metadata()


# Preparar ui

st.title(":flag-co: Búsqueda en Planes Anuales de Adquisición")

st.markdown(
    """Aplicación para encontrar similitud semántica en descripción de Planes Anuales de Adquisición."""
)

st.markdown("---")

opt_entidades = st.multiselect("Seleccione entidades", df_meta["entidad"])

query = st.text_input("Consulta a realizar")


# Aca se modifica todo

embedder = load_embedder(MODELO)

df_entidades = crear_df_entidades()

if opt_entidades and query:
    df_filtrado = df_meta[df_meta["entidad"].isin(opt_entidades)]

    dfs = []

    for row in df_filtrado.itertuples():
        df = pd.read_excel(
            dir_data.joinpath("paa", row.archivo),
            skiprows=1,
        )
        df.rename(RENOMBRES, inplace=True, axis=1)
        df = df[COLS_PLANES]
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

                seleccion = seleccion.applymap(lambda x: x if x else "No Identificado")

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
