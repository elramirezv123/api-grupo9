import base64
import hmac
import hashlib
import urllib
import datetime
from bodega.constants.config import apiKey
from bodega.models import Log
import pytz

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


def toMiliseconds(minutes):
    start = (datetime.datetime.now().replace(tzinfo=pytz.UTC) - datetime.datetime(1970,1,1).replace(tzinfo=pytz.UTC)).total_seconds()
    return int((start + minutes*60)*1000)

def logger(caller_name, comment):
    now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
    log_entity= Log.objects.create(caller=caller_name,
                                     comment=comment,
                                     created_at=now)
    log_entity.save()


def validate_post_body(body):
    valid_keys = ['almacenId', 'sku', 'cantidad', 'oc']
    return set(body.keys()) == set(valid_keys)