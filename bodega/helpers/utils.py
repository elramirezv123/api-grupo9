import base64
import hmac
import hashlib
import urllib
from bodega.constants.config import apiKey

'''
Este módulo es para las funciones que son transversalmente útiles para
todos los módulos.
'''

# https://sites.google.com/site/studyingpython/home/basis/hmac-sha1
def hashQuery(query):
    '''
    Función para hashear la query junto a la apiKey,
    retorna el hash en forma de string que se debe colocar en el header
    de la forma: Authorization: INTEGRACION grupo9: hash
    '''
    query = str.encode(query)
    sharedKey = str.encode(apiKey)
    hash = hmac.new(sharedKey, query, hashlib.sha1).digest()
    b = base64.encodestring(hash)
    return b.rstrip().decode("utf-8")

