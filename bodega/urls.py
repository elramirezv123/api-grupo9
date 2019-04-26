from django.urls import path
from django.conf.urls import url

from . import views
'''
En este módulo se van registrando las URL's para poder hacer las llamadas
a nuestra API. La idea es hacerlo igual a como está descrito en la documentación.
'''

urlpatterns = [
    path('inventario', views.inventario),
    path('pedidos', views.new_pedido),
    url(r'pedidos/(?P<almacenId>\D+)',views.pedidos),
    path('orders', views.orders),
]