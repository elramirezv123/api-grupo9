from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    path('inventario', views.inventario),
    path('pedidos', views.new_pedido),
    url(r'pedidos/(?P<almacenId>\D+)/',views.pedidos),
    path('orders', views.orders),
]