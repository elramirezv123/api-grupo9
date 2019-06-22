from rest_framework import serializers
from .models import Product, Ingredient



class IngredientSerializer(serializers.ModelSerializer):
    sku_product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    sku_ingredient = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    class Meta:
        model = Ingredient
        fields = ("sku_product", "sku_ingredient", "production_batch", "volume_in_store", "for_batch")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("sku", "name", "price", "batch", "productors", "ingredientes")