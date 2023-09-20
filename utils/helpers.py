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
