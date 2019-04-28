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
    ingredients = models.ManyToManyField("self", related_name='ingredientes', symmetrical=False, through="Ingredient")

    def __str__(self):
        """A string representation of the model."""
        return self.name


class Ingredient(models.Model):
    sku_product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                        related_name="sku_product")
    sku_ingredient = models.ForeignKey(Product, on_delete=models.CASCADE,
                                        related_name="sku_ingredient")

    quantity = models.DecimalField(decimal_places=2, max_digits=6)
    production_batch = models.IntegerField()
    quantity_batch = models.DecimalField(decimal_places=2, max_digits=6)
    volume_in_store = models.IntegerField()



class Request(models.Model):
    store_destination_id = models.CharField(max_length=255)
    sku_id = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)

    def __str__(self):
        """A string representation of the model."""
        return str(self.sku_id) + str(self.amount)
