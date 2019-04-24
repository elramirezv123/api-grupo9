from django.urls import path

from . import views

urlpatterns = [
    path('inventario', views.inventario),
]