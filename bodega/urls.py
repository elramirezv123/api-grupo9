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
router.register(r'ingredients', products_views.IngredientViewSet)

urls = [
    path('inventories', api_views.inventories),
    path('orders', api_views.orders),
    url(r'orders/(?P<cantidad>\D+)',api_views.orders),
    path('watch_server', api_views.watch_server_view),
    path('check_not_initiated', api_views.check_not_initiated_view),
    path('check_not_finished', api_views.check_not_finished_view),
    path('test', api_views.test),
    path('orders2', api_views.orders2),

]

urlpatterns = [*router.urls,
            path('almacenes', control_views.almacenes_info),
            path('inventario', control_views.inventory_info),
            path('pedir', control_views.pedir),
            path('empty_reception', control_views.empty_reception_view),
            path('empty_pulmon', control_views.empty_pulmon_view),
            path('preparar', control_views.preparar),
            path('ftp', control_views.ftp_info),
            path('logs', control_views.show_logs),
            path('b2b', control_views.show_b2b_logs),
            path('ask/<group>/<sku>', control_views.ask_group)]
