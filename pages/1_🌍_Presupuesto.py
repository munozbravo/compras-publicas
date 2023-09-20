import pandas as pd
import plotly.express as px
import streamlit as st

from data.rutas import PGN2024
from utils.caches import cargar_df
from utils.config import configurar_pagina
from utils.variables import TIPO_PRESUPUESTO, COLS_PGN


configurar_pagina("Presupuesto de entidades estatales", "🌍", "wide")


# Preparar ui

st.title(":flag-co: Presupuesto de entidades estatales")

st.markdown("""Presupuesto General de la Nación vigencia 2024.""")

st.markdown("---")


df_pgn = cargar_df(
    PGN2024, tipos=None, columnas=COLS_PGN, ordenar="TOTAL", ascending=False
)

for col in ["APORTE_NACIONAL", "RECURSOS_PROPIOS", "TOTAL"]:
    df_pgn[col] = df_pgn[col].str.replace(",", "")
    df_pgn[col] = pd.to_numeric(df_pgn[col])

df_pgn = df_pgn[df_pgn["nivel"] == "total"]

df_inversion = df_pgn[df_pgn["nivel"] == "partida"]

tipo = st.selectbox("Seleccione tipo de presupuesto 👇", TIPO_PRESUPUESTO)

df_tipo = df_pgn[df_pgn["tipo"] == tipo]

fig = px.treemap(
    df_tipo,
    path=[px.Constant("Todos"), "ENTIDAD"],
    values="TOTAL",
    color="ENTIDAD",
)

fig.update_traces(
    root_color="lightgrey",
    hovertemplate="<b>%{label}</b><br><b>Monto</b> %{value:,.2f}",
    texttemplate="<b>%{label}</b><br><b>Monto</b> %{value:,.2f}",
    textinfo="label+value",
)

st.plotly_chart(fig, use_container_width=True)


# Esto era lo anterior donde cruzaba para obtener sector

# df_entidades = cargar_df(
#     ENTIDADES, tipos={"CCB_NIT_INST": str}, columnas=COLS_ENTIDADES
# )

# session = create_session(TOKEN)

# prep_ppa = payload_paa(2023, limit=OFFSET)
# paas = buscar_socrata(_session=session, url=URL_PAA, payload=prep_ppa, offset=OFFSET)

# if paas:
#     df_paa = pd.DataFrame.from_records(paas)

#     df_paa["valor_presupuesto_general"] = pd.to_numeric(
#         df_paa["valor_presupuesto_general"]
#     )

#     df_paa["normalizado"] = normalizar_textual(df_paa, "nombre_entidad")
#     df_entidades["normalizado"] = normalizar_textual(df_entidades, "NOMBRE")

#     df_paa = df_paa.merge(
#         df_entidades, how="left", left_on="normalizado", right_on="normalizado"
#     )

#     cols = COLS_ENTIDADES + ["nombre_entidad"]
#     df_paa[cols] = df_paa[cols].fillna("No identificado")

#     fig = px.treemap(
#         df_paa,
#         path=[px.Constant("Todos"), "SECTOR", "nombre_entidad"],
#         values="valor_presupuesto_general",
#         color="SECTOR",
#     )

#     fig.update_traces(
#         root_color="lightgrey",
#         hovertemplate="<b>%{label}</b><br><b>Monto</b> %{value:,.2f}",
#         texttemplate="<b>%{label}</b><br><b>Monto</b> %{value:,.2f}",
#         textinfo="label+value",
#     )

#     st.plotly_chart(fig, use_container_width=True)
