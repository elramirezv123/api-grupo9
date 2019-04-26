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