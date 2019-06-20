# Constantes útiles

# Umbral, se pedirá si es que tenemos menos de stock_minimo + DELTA
DELTA = 0
# Factor de multiplicación para pedidos
REQUEST_FACTOR = 10

headers = {'Content-Type': 'application/json'}

# sku_products = [1001, 1002, 1004, 1008, 1009, 1010, 1013, 1016]

sku_products =  [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016]

# esta en lotes, no en cantidades
minimum_stock = [
    1101,
    1105,
    1106,
    1107,
    1108,
    1109,
    1110,
    1111,
    1112,
    1114,
    1115,
    1116,
    1201,
    1207,
    1209,
    1210,
    1211,
    1215,
    1216,
    1301,
    1307,
    1309,
    1310,
    1407
]

# base_minimum_stock = {
# "1003": 50,
# "1005": 50,
# "1006": 50,
# "1007": 50,
# "1011": 50,
# "1012": 50,
# "1014": 50,
# "1015": 50
# }

base_minimum_stock = {}

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
    "recepcion": 549,
    "pulmon": 100000399,
    "cocina": 1377,
    "libre1": 4586,
    "libre2": 1385, 
    "despacho": 177
}