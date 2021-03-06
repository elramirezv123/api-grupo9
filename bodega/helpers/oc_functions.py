from .utils import hashQuery
from bodega.constants.logic_constants import *
from bodega.constants.config import *
from bodega.helpers.utils import toMiliseconds
from bodega.models import PurchaseOrder
import requests
import json
import xml.etree.ElementTree as ET
import pysftp
import datetime
import pytz


def deleteOc(ocId, reason):
    body = {"anulacion": reason}
    response = requests.delete(
        ocURL + "anular/{}".format(ocId), headers=headers, json=body)
    return response.json()


def newOc(clientId, vendorId, sku, delivery_date, quantity, unitPrice, channel, notURL="https://tuerca9.ing.puc.cl"):

    body = {
        "cliente": clientId,
        "proveedor": vendorId,
        "sku": sku,
        "fechaEntrega": toMiliseconds(delivery_date),
        "cantidad": int(quantity),
        "precioUnitario": int(unitPrice) if int(unitPrice) > 0 else 10,
        "canal": channel,
        "notas": "Yupi",
        "urlNotificacion": notURL
    }
    response = requests.put(ocURL + "crear", headers=headers, json=body)
    return response.json()


def getOc(ocId):
    response = requests.get(ocURL + "obtener/{}".format(ocId), headers=headers)
    return response.json()


def receiveOc(ocId):
    body = {"id": ocId}
    response = requests.post(
        ocURL + "recepcionar/{}".format(ocId), headers=headers, json=body)
    
    return response.json()


def declineOc(ocId, reason):
    body = {"rechazo": reason}
    response = requests.post(
        ocURL + "rechazar/{}".format(ocId), headers=headers, json=body)
    return response.json()


def updateOC(idOc, state):
    order = PurchaseOrder.objects.filter(oc_id=idOc)
    order.update(state=state)

def anular_vencidas():
    ftp_orders = PurchaseOrder.objects.filter(channel='b2b')
    now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
    for order in ftp_orders:
        if order.deadline < now:
            deleteOc(order.oc_id, 'Orden de compra vencida')