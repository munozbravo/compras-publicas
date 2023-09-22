from datetime import date, timedelta

import pandas as pd


def normalizar_textual(df: pd.DataFrame, col: str) -> pd.Series:
    """Normaliza una columna textual de un DataFrame

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame que contiene la columna
    col : str
        Columna a normalizar

    Returns
    -------
    pd.Series
        Serie normalizada
    """
    normalizada = (
        df[col]
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )

    return normalizada


def validar_fechas(fechas: tuple | date = None) -> tuple[date]:
    """Comprueba retorno de fechas inicial y final

    Parameters
    ----------
    fechas : tuple | date, optional
        Fechas inicial y final, default None

    Returns
    -------
    tuple
        Fechas inicial y final
    """
    if isinstance(fechas, tuple):
        if len(fechas) == 2:
            inicio, fin = fechas
        elif len(fechas) == 1:
            inicio = fechas[0]
            fin = date.today()
        else:
            fin = date.today()
            inicio = fin - timedelta(days=1)
    elif isinstance(fechas, date):
        inicio = fechas
        fin = date.today()
    else:
        fin = date.today()
        inicio = fin - timedelta(days=1)

    return (inicio, fin)
