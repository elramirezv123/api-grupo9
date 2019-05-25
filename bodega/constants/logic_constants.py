# Constantes útiles

# Umbral, se pedirá si es que tenemos menos de stock_minimo + DELTA
DELTA = 0
# Factor de multiplicación para pedidos
REQUEST_FACTOR = 10

headers = {'Content-Type': 'application/json'}

sku_products = [1001, 1009, 1010, 1014, 1016]

# esta en lotes, no en cantidades
minimum_stock = {
    "1301": 50,
    "1201": 250,
    "1209": 20,
    "1109": 50,
    "1309": 170,
    "1106": 400,
    "1114": 50,
    "1215": 20,
    "1115": 30,
    "1105": 50,
    "1013": 300,
    "1216": 50,
    "1116": 250,
    "1110": 80,
    "1310": 20,
    "1210": 150,
    "1112": 130,
    "1108": 10,
    "1407": 40,
    "1207": 20,
    "1107": 50,
    "1307": 170,
    "1211": 60
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