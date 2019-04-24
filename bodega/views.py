from django.shortcuts import render
from django.http import JsonResponse
from .utils import hashQuery
import requests


# Create your views here.

def inventario(request):
    response = {
        "name": "grupo9",
        "cantidad_productos": "",
        "inventario": ""
    }

    return JsonResponse(response)
