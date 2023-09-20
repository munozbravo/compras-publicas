from datetime import date, timedelta

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
import streamlit as st


from utils.caches import create_session, buscar_socrata, crear_df_resultados
from utils.config import configurar_pagina
from utils.socrata import payload_proponentes
from utils.variables import URL_PROPONENTES, COLS_PROVEEDORES


configurar_pagina(
    title="Proponentes en contratación pública", icon="🧑‍💼", layout="wide"
)


# Definir variables y constantes

TOKEN = st.secrets["X_APP_TOKEN"]

COLS_NA = ["proveedor"]
COLS_DUP = ["proveedor", "id_procedimiento"]

OFFSET = 1000

HOY = date.today()
ayer = HOY - timedelta(days=30)

session = create_session(TOKEN)

k1 = "proveedores"

if k1 not in st.session_state:
    st.session_state[k1] = []


# Preparar ui


st.title(":flag-co: Búsqueda de proponentes en contratación")

st.markdown("""Búsqueda de proponentes en procesos de contratación.""")

st.markdown("---")


with st.sidebar:
    fechas = st.date_input("Rango de fechas", [ayer, HOY], max_value=HOY)

    proveedor = st.text_input("Proveedor a buscar")

    boton = st.button("Buscar proveedores")


if boton:
    if proveedor:
        payload = payload_proponentes(fechas=fechas, offset=OFFSET, proveedor=proveedor)
    else:
        payload = payload_proponentes(fechas=fechas, offset=OFFSET)

    resultados = buscar_socrata(
        _session=session, url=URL_PROPONENTES, payload=payload, offset=OFFSET
    )

    st.session_state[k1] = [
        {k: res.get(k) for k in res.keys() if k in COLS_PROVEEDORES}
        for res in resultados
    ]

    n = len(st.session_state[k1])

    inicio, fin = fechas
    st.info(
        f'Búsqueda entre {inicio.strftime("%Y-%m-%d")} y {fin.strftime("%Y-%m-%d")}.',
        icon="ℹ️",
    )
    st.info(f"{n} registros encontrados.", icon="🔥")


if st.session_state[k1]:
    df_proveedores = crear_df_resultados(
        st.session_state[k1], na_cols=COLS_NA, dup_cols=COLS_DUP
    )

    df_proveedores = df_proveedores[COLS_PROVEEDORES]

    gb = GridOptionsBuilder.from_dataframe(df_proveedores)
    gb.configure_column(field="nit_proveedor", hide=True, supress_tool_panel=True)

    gb.configure_selection(selection_mode="single", use_checkbox=False)
    gridOptions = gb.build()

    grid = AgGrid(
        df_proveedores,
        gridOptions,
        height=350,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
    )
