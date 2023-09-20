import streamlit as st


def configurar_pagina(title: str, icon: str, layout: str = "wide"):
    """Iniciar configuracion de página.

    Parameters
    ----------
    title : str
        Nombre de la página
    icon : str
        Icono de la página
    layout : str
        Layout inicial de la página
    """

    return st.set_page_config(page_title=title, page_icon=icon, layout=layout)
