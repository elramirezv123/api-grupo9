from django.db import models
from django.template.defaultfilters import slugify

# Create your models here.


class Product(models.Model):
    sku = models.IntegerField(primary_key=True)
    name = models.TextField()
    description = models.TextField()
    price = models.IntegerField(null=True)
    slug = models.SlugField(unique=True, max_length=255)
    duration = models.DecimalField(
        null=True, decimal_places=2, max_digits=6)
    equivalence = models.DecimalField(
        null=True, decimal_places=3, max_digits=6)
    unit = models.CharField(max_length=255, null=True)
    batch = models.IntegerField(null=True)
    production_time = models.IntegerField(null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """A string representation of the model."""
        return self.name


class Ingredient(models.Model):
    name = models.TextField()
    slug = models.SlugField(unique=True, max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """A string representation of the model."""
        return self.name


class Request(models.Model):
    store_destination_id = models.CharField(max_length=255)
    sku_id = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)

    def __str__(self):
        """A string representation of the model."""
        return str(self.sku_id) + str(self.amount)
