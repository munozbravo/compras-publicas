from datetime import date, timedelta

import streamlit as st


# Definir variables y constantes

TOKEN = st.secrets["X_APP_TOKEN"]

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

OFFSET = 1000

HOY = date.today()
ayer = HOY - timedelta(days=7)


# Preparar ui

st.set_page_config(page_title="Observatorio de Mercado", page_icon="👋", layout="wide")

st.title(":flag-co: Observatorio de mercado")

st.sidebar.success("Seleccione alguna de las pestañas disponibles.")

st.markdown(
    """**👈 Seleccione alguna pestaña** para diferentes análisis.
    """
)

st.markdown("---")
