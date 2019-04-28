from django.db import models
from django.template.defaultfilters import slugify

# Create your models here.

class Product(models.Model):
    sku = models.CharField(primary_key=True, max_length=255)
    Nombre = models.TextField()
    Descripcion = models.TextField()
    slug = models.SlugField(unique=True, max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """A string representation of the model."""
        return self.Nombre

class Ingredient(models.Model):
    Nombre = models.TextField()
    slug = models.SlugField(unique=True, max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """A string representation of the model."""
        return self.Nombre

class Pedidos(models.Model):
    almacen_destino_id = models.CharField(max_length=255)
    sku_id = models.CharField(max_length=255)
    cantidad = models.CharField(max_length=255)

    def __str__(self):
        """A string representation of the model."""
        return str(self.sku_id) + str(self.cantidad)