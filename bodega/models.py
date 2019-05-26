from django.db import models
from django.template.defaultfilters import slugify

# Create your models here.


class Product(models.Model):
    sku = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    cost = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    used_by = models.IntegerField()
    duration = models.DecimalField(decimal_places=2, max_digits=6)
    batch = models.IntegerField()
    production_time = models.IntegerField()
    productors = models.CharField(max_length=100)
    p_type = models.CharField(max_length=100)
    ingredients = models.ManyToManyField("self", related_name='ingredientes', symmetrical=False, through="Ingredient", through_fields=("sku_ingredient", "sku_product"))


class Ingredient(models.Model):
    sku_product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                        related_name="sku_product")
    sku_ingredient = models.ForeignKey(Product, on_delete=models.CASCADE,
                                        related_name="sku_ingredient")

    production_batch = models.IntegerField()
    volume_in_store = models.IntegerField()



class Request(models.Model):
    store_destination_id = models.CharField(max_length=255)
    sku_id = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)
    group = models.IntegerField(null=True)
    state = models.CharField(max_length=255, default="processing")
    accepted = models.BooleanField(default=False)
    dispatched = models.BooleanField(default=False)
    deadline = models.DateField(null=True)

    def __str__(self):
        """A string representation of the model."""
        return str(self.sku_id) + str(self.amount)


class PurchaseOrder(models.Model):
    oc_id = models.CharField(primary_key=True, max_length=255)
    sku = models.IntegerField()
    client = models.CharField(max_length=255)
    provider = models.CharField(max_length=255)
    amount = models.IntegerField()
    price = models.IntegerField()
    state = models.CharField(default="creada", max_length=255)
    channel = models.CharField(max_length=255)
    deadline = models.DateTimeField()  #maximo tiempo de espera

class File(models.Model):
    filename = models.CharField(max_length=255)
    processed = models.BooleanField(default=False)  
    attended = models.BooleanField(default=False)