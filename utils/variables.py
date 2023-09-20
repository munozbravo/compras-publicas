# manuales
ORDEN_ENTIDAD = ["Nacional", "Territorial", "Corporación Autónoma"]

TIPO_PRESUPUESTO = ["Funcionamiento", "Inversión", "Total de Entidad"]

# IDs Colombia Compra Eficiente

ID_PROCESOS = "p6dx-8zbt"  # SECOP II - Procesos de Contratación
ID_ENCABEZADO_PAA = "b6m4-qgqv"  # SECOP II - PAA - Encabezado
ID_OFERTAS = "wi7w-2nvm"  # SECOPII - Ofertas Por Proceso
ID_PROPONENTES = "hgi6-6wh3"  # Proponentes por Proceso SECOP II
ID_SECOP1_PROCESOS = "f789-7hwg"  # SECOP I - Procesos de Compra Pública
ID_INTEGRADO = "rpmr-utcd"  # SECOP Integrado
ID_ENTIDADES_SECOP = "pajg-ux27"  # Entidades con Publicación en SECOP II
ID_CONTRATOS = "jbjy-vk9h"  # contratos registrados en SECOP II desde su lanzamiento


# IDs Función Pública

ID_ENTIDADES_FP = "h7zv-k39x"  # Universo de entidades

# URLs
URL_RESOURCES = "https://www.datos.gov.co/resource/"

URL_PROCESOS = f"{URL_RESOURCES}{ID_PROCESOS}.json"
URL_PAA = f"{URL_RESOURCES}{ID_ENCABEZADO_PAA}.json"
URL_ENTIDADES_FP = f"{URL_RESOURCES}{ID_ENTIDADES_FP}.json"
URL_ENTIDADES_SECOP = f"{URL_RESOURCES}{ID_ENTIDADES_SECOP}.json"
URL_PROPONENTES = f"{URL_RESOURCES}{ID_PROPONENTES}.json"

# Columnas de tablas

COLS_PROCESOS = [
    "id_del_proceso",
    "descripci_n_del_procedimiento",
    "entidad",
    "precio_base",
    "fecha_de_publicacion_del",
    "fase",
    "duracion",
    "unidad_de_duracion",
    "modalidad_de_contratacion",
    "estado_del_procedimiento",
    "estado_de_apertura_del_proceso",
    "referencia_del_proceso",
    "nit_entidad",
    "ordenentidad",
    "adjudicado",
    "fecha_adjudicacion",
    "nombre_del_proveedor",
    "urlproceso",
]


COLS_ENTIDADES = ["NOMBRE", "CCB_NIT_INST", "ORDEN", "SECTOR"]

COLS_PGN = [
    "tipo",
    "nivel",
    "CONCEPTO",
    "ENTIDAD",
    "APORTE_NACIONAL",
    "RECURSOS_PROPIOS",
    "TOTAL",
]


COLS_PAA = [
    "descripcion",
    "mes_inicio",
    "mes_oferta",
    "duracion",
    "intervalo",
    "modalidad",
    "fuente",
    "valor",
    "unidad",
    "ubicacion",
    "unspsc",
]

COLS_PROVEEDORES = [
    "proveedor",
    "nit_proveedor",
    "id_procedimiento",
    "fecha_publicaci_n",
    "nombre_procedimiento",
    "entidad_compradora",
]
