# Constantes útiles
# DEV
prod = False
apiKey = "R&FTHQi3AkqUx%6"
apiURL = "https://integracion-2019-dev.herokuapp.com/bodega/"
ocURL = "https://integracion-2019-dev.herokuapp.com/oc/docs/"

# PRODUCTION
# apiKey = "R&FTHQi3AkqUx%6"
# apiURL = "https://integracion-2019-prod.herokuapp.com/bodega/"


# Umbral, se pedirá si es que tenemos menos de stock_minimo + DELTA
DELTA = 0
# Factor de multiplicación para pedidos
REQUEST_FACTOR = 10

# Estos son los ids de los almacenes del grupo, podemos guardarlos o no en la base de datos.
# Pero creo que lo mejor es si o si guardarlos en algún lado para ahorrarnos la consulta a la API.
# Almacenes id de desarrollo
# almacenes = {
#     "recepcion": "5cbd3ce444f67600049431e3",
#     "pulmon":"5cbd3ce444f67600049431e7",
#     "cocina": "5cbd3ce444f67600049431e8",
#     "libre1": "5cbd3ce444f67600049431e5",
#     "libre2": "5cbd3ce444f67600049431e6",
#     "despacho":"5cbd3ce444f67600049431e4",
# }

# Almacenes id para produccion

almacenes = {
    "recepcion": "5cc7b139a823b10004d8e6fd",
    "pulmon": "5cc7b139a823b10004d8e701",
    "cocina": "5cc7b139a823b10004d8e702",
    "libre1": "5cc7b139a823b10004d8e700",
    "despacho": "5cc7b139a823b10004d8e6fe",
}

headers = {'Content-Type': 'application/json'}


sku_products = [1001, 1009, 1010, 1014, 1016]

minimum_stock = {
    "1301": 5,
    "1201": 25,
    "1209": 2,
    "1109": 5,
    "1309": 5,
    "1106": 10,
    "1114": 5,
    "1215": 2,
    "1115": 3,
    "1105": 5,
    "1013": 6,
    "1216": 5,
    "1116": 25,
    "1110": 8,
    "1310": 2,
    "1210": 15,
    "1112": 13,
    "1108": 1,
    "1407": 4,
    "1207": 2,
    "1107": 5,
    "1307": 5,
    "1211": 6
}


#{sku:[suma, numero_items]}

prom_request= {
    "1301": [],
    "1201": [],
    "1209":[],
    "1109": [],
    "1309": [],
    "1106": [],
    "1114": [],
    "1215": [],
    "1115": [],
    "1105": [],
    "1013": [],
    "1216": [],
    "1116": [],
    "1110": [],
    "1310": [],
    "1210": [],
    "1112": [],
    "1108": [],
    "1407": [],
    "1207": [],
    "1107": [],
    "1307": [],
    "1211": []
}

almacen_stock = {
    "recepcion": 130,
    "pulmon": 99999999,
    "cocina": 1099,
    "libre1": 3142,
    "libre2": 535, 
    "despacho": 100
}

# Ambiente de desarrollo 
id_grupos = {
    '1': '5cbd31b7c445af0004739be3',
    '2': '5cbd31b7c445af0004739be4',
    '3': '5cbd31b7c445af0004739be5',
    '4': '5cbd31b7c445af0004739be6',
    '5': '5cbd31b7c445af0004739be7',
    '6': '5cbd31b7c445af0004739be8',
    '7': '5cbd31b7c445af0004739be9',
    '8': '5cbd31b7c445af0004739bea',
    '9': '5cbd31b7c445af0004739beb',
    '10': '5cbd31b7c445af0004739bec',
    '11': '5cbd31b7c445af0004739bed',
    '12': '5cbd31b7c445af0004739bee',
    '13': '5cbd31b7c445af0004739bef',
    '14': '5cbd31b7c445af0004739be0'
}

# Ambiente producción 

# id_grupos = {
#     '1': '5cc66e378820160004a4c3bc',
#     '2': '5cc66e378820160004a4c3bd',
#     '3': '5cc66e378820160004a4c3be',
#     '4': '5cc66e378820160004a4c3bf',
#     '5': '5cc66e378820160004a4c3c0',
#     '6': '5cc66e378820160004a4c3c1',
#     '7': '5cc66e378820160004a4c3c2',
#     '8': '5cc66e378820160004a4c3c3',
#     '9': '5cc66e378820160004a4c3c4',
#     '10': '5cc66e378820160004a4c3c5',
#     '11': '5cc66e378820160004a4c3c6',
#     '12': '5cc66e378820160004a4c3c7',
#     '13': '5cc66e378820160004a4c3c8',
#     '14': '5cc66e378820160004a4c3c09'
# }


