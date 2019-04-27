from django.db import models
from django.template.defaultfilters import slugify

# Create your models here.

class Product(models.Model):
    sku = models.CharField(primary_key=True, max_length=255)
    Nombre = models.TextField()
    Descripcion = models.TextField()
    slug = models.SlugField(unique=True, max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)

class Ingredient(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    Nombre = models.TextField()
    slug = models.SlugField(unique=True, max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)