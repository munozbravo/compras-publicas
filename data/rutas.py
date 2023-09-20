from pathlib import Path


# Directorios

DIR_DATA = Path(__file__).parent

DIR_PAA = DIR_DATA.joinpath("paa")


# Filepaths

ENTIDADES = DIR_DATA.joinpath("entidades", "entidades.csv")

PGN2024 = DIR_DATA.joinpath("presupuesto", "pgn2024.csv")

META_PAA = DIR_DATA.joinpath("metadata", "paa.xlsx")
