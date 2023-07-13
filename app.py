import json
import os

from sentence_transformers import SentenceTransformer, util
import numpy as np
import pandas as pd
import requests
import streamlit as st


app_token = os.getenv("X_APP_TOKEN")

modelo = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

embedder = SentenceTransformer(modelo)

if app_token:
    st.write("Token cargado")

query = st.text_input("Consulta a realizar")
if query:
    st.write(f"Se va a buscar la frase: {query}")

if embedder:
    st.write("SentenceTransformer cargado")
