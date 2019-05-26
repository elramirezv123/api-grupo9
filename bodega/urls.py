from django.urls import path
from django.conf.urls import url

from .views import api_views, control_views, products_views
from rest_framework.routers import DefaultRouter
'''
En este módulo se van registrando las URL's para poder hacer las llamadas
a nuestra API. La idea es hacerlo igual a como está descrito en la documentación.
'''

router = DefaultRouter()

router.register(r'products', products_views.ProductViewSet)

urls = [
    path('inventories', api_views.inventories),
    path('orders', api_views.orders),
    url(r'orders/(?P<cantidad>\D+)',api_views.orders),
    path('test', api_views.test),

]

urlpatterns = [*router.urls,
            path('almacenes', control_views.almacenes_info),
            path('inventario', control_views.inventory_info),
            path('pedir', control_views.pedir)]