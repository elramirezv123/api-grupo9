# Constantes útiles

apiKey = "R&FTHQi3AkqUx%6" 
apiURL = "https://integracion-2019-dev.herokuapp.com/bodega/"


# Estos son los ids de los almacenes del grupo, podemos guardarlos o no en la base de datos.
# Pero creo que lo mejor es si o si guardarlos en algún lado para ahorrarnos la consulta a la API.
almacenes = {
    "recepcion": "5cbd3ce444f67600049431e3",
    "pulmon":"5cbd3ce444f67600049431e7",
    "despacho":"5cbd3ce444f67600049431e4",
    "cocina": "5cbd3ce444f67600049431e8",
    "libre1": "5cbd3ce444f67600049431e5",
    "libre2": "5cbd3ce444f67600049431e6"
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
