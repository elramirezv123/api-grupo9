from rest_framework import viewsets
from bodega.models import Product, Ingredient
from django.shortcuts import get_object_or_404
from bodega.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer