from datetime import date, timedelta

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
import streamlit as st


from utils.caches import create_session, buscar_socrata, crear_df_resultados
from utils.config import configurar_pagina
from utils.helpers import validar_fechas
from utils.socrata import payload_proponentes, payload_procesos
from utils.variables import (
    COLS_PROVEEDORES,
    COLS_PROCESOS,
    URL_PROPONENTES,
    URL_PROCESOS,
)


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
    inicio, fin = validar_fechas(fechas)

    if proveedor:
        payload = payload_proponentes(
            fechas=(inicio, fin), offset=OFFSET, proveedor=proveedor
        )
    else:
        payload = payload_proponentes(fechas=(inicio, fin), offset=OFFSET)

    resultados = buscar_socrata(
        _session=session, url=URL_PROPONENTES, payload=payload, offset=OFFSET
    )

    st.session_state[k1] = [
        {k: res.get(k) for k in res.keys() if k in COLS_PROVEEDORES}
        for res in resultados
    ]

    n = len(st.session_state[k1])

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

    gb.configure_selection(selection_mode="single", use_checkbox=True)
    gridOptions = gb.build()

    grid = AgGrid(
        df_proveedores,
        gridOptions,
        height=250,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
    )

    selected_rows = grid["selected_rows"]

    for fila in selected_rows:
        id_proceso = fila.get("id_procedimiento")

        pay = payload_procesos(id_proceso=id_proceso)
        res = buscar_socrata(_session=session, url=URL_PROCESOS, payload=pay)
        res = [
            {k: proceso.get(k) for k in proceso.keys() if k in COLS_PROCESOS}
            for proceso in res
        ]
        if res:
            resultado = res[0]

            adjudicado = resultado.get("adjudicado")
            color_adjud = "green" if adjudicado == "Si" else "red"

            st.markdown(
                f"""
                    ## Descripción
                    {resultado.get('descripci_n_del_procedimiento')}

                    Entidad: :blue[{resultado.get('entidad')}]

                    Valor: :blue[{float(resultado.get('precio_base')):,.2f}]

                    Duración: {resultado.get('duracion')} {resultado.get('unidad_de_duracion')}

                    Publicado: {resultado.get('fecha_de_publicacion_del')}
                    
                    Modalidad: {resultado.get('modalidad_de_contratacion')}

                    Adjudicado: :{color_adjud}[{adjudicado}]

                    [URL del proceso]({resultado.get('urlproceso').get('url')})
                """
            )

            if adjudicado == "Si":
                st.markdown(f"Proveedor: {resultado.get('nombre_del_proveedor')}")
