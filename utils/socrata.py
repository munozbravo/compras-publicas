from datetime import date

from utils.helpers import validar_fechas


def payload_procesos(
    fechas: tuple[date] | date = None,
    precio_minimo: int = 0,
    offset: int = 1000,
    orden: str = None,
    entidades: list | set = None,
    id_proceso: str = None,
    sort: str = None,
) -> dict:
    """Payload para SECOP II - Procesos de Contratación

    Parameters
    ----------
    fechas : tuple[date] | date, optional
        Fechas inicial y final de búsqueda, default None
    precio_minimo : int, optional
        Precio mínimo de proceso de contratación, default 0
    offset : int, optional
        Cantidad de resultados por llamado, default 1000
    orden : str, optional
        Entidad de orden Nacional o Territorial, default None
    entidades : list | set, optional
        Filtro de entidades a buscar, default None
    id_proceso : str, optional
        ID de proceso a buscar, default None
    sort : str, optional
        Campo a usar para ordenar, default None

    Returns
    -------
    dict
        Payload para enviar a Socrata API
    """
    # https://dev.socrata.com/foundry/www.datos.gov.co/p6dx-8zbt

    payload = {"$limit": offset}

    if sort is not None:
        payload.update({"$order": sort})

    where_query = ""

    if fechas is not None:
        inicio, fin = validar_fechas(fechas)

        inicial = f'{inicio.strftime("%Y-%m-%d")}T00:00:00'
        final = f'{fin.strftime("%Y-%m-%d")}T23:59:59'

        q = f"fecha_de_publicacion_del between '{inicial}' and '{final}'"

        where_query = f"{where_query} AND {q}" if where_query else q

    if precio_minimo > 0:
        q = f"precio_base > {precio_minimo}"

        where_query = f"{where_query} AND {q}" if where_query else q

    if orden is not None:
        q = f"ordenentidad = '{orden}'"

        where_query = f"{where_query} AND {q}" if where_query else q

    if entidades is not None:
        q = f"entidad in{tuple(e for e in entidades)}"

        where_query = f"{where_query} AND {q}" if where_query else q

    if id_proceso is not None:
        q = f"id_del_proceso = '{id_proceso}'"

        where_query = f"{where_query} AND {q}" if where_query else q

    if where_query:
        payload.update({"$where": where_query})

    return payload


def payload_paa(anno: int = None, limit: int = 1000) -> dict:
    """Payload para SECOP II - PAA - Encabezado

    Parameters
    ----------
    anno : int, optional
        Año deseado para búsqueda, default None

    limit : int, optional
        Cantidad de registros por llamado, default 1000

    Returns
    -------
    dict
        Payload para enviar a Socrata API
    """
    # https://dev.socrata.com/foundry/www.datos.gov.co/b6m4-qgqv

    payload = {"$limit": limit}
    where_query = ""

    if anno is not None:
        where_query = f"anno = {anno}"

    if where_query:
        payload.update({"$where": where_query})

    return payload


def payload_entidades(offset=1000, selection=None, select_col=None, sort=None):
    # https://dev.socrata.com/foundry/www.datos.gov.co/h7zv-k39x
    # https://dev.socrata.com/foundry/www.datos.gov.co/pajg-ux27

    payload = {"$limit": offset}

    if sort is not None:
        payload.update({"$order": sort})

    where_query = ""

    if (selection is not None) and (select_col is not None):
        if isinstance(selection, list):
            selection = set(selection)
        where_query = f"{select_col} in{tuple(e for e in selection)}"

    if where_query:
        payload.update({"$where": where_query})

    return payload


def payload_proponentes(
    fechas: tuple[date] | date,
    offset: int = 1000,
    id_proc: str = None,
    proveedor: str = None,
) -> dict:
    """Payload para Proponentes por Proceso SECOP II

    Parameters
    ----------
    fechas : tuple[date] | date
        Fechas inicial y final de búsqueda
    offset : int, optional
        Cantidad de resultados por llamado, default 1000
    id_proc : str, optional
        ID del proceso de compra, default None
    proveedor : str, optional
        Nombre del proveedor a buscar, default None

    Returns
    -------
    dict
        Payload para enviar a Socrata API
    """
    # https://dev.socrata.com/foundry/www.datos.gov.co/hgi6-6wh3

    payload = {"$limit": offset, "$order": "fecha_publicaci_n DESC"}

    inicio, fin = validar_fechas(fechas)

    inicial = f'{inicio.strftime("%Y-%m-%d")}T00:00:00'
    final = f'{fin.strftime("%Y-%m-%d")}T23:59:59'

    where_query = f"fecha_publicaci_n between '{inicial}' and '{final}'"

    if id_proc is not None:
        where_query = f"{where_query} AND id_procedimiento = '{id_proc}'"

    if proveedor is not None:
        provee = "%".join(proveedor.split())
        where_query = f"{where_query} AND upper(proveedor) like upper('%{provee}%')"

    if where_query:
        payload.update({"$where": where_query})

    return payload
