# Generated by Django 2.2 on 2019-05-23 23:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('production_batch', models.IntegerField()),
                ('volume_in_store', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_destination_id', models.CharField(max_length=255)),
                ('sku_id', models.CharField(max_length=255)),
                ('amount', models.CharField(max_length=255)),
                ('group', models.IntegerField(null=True)),
                ('state', models.CharField(default='processing', max_length=255)),
                ('accepted', models.BooleanField(default=False)),
                ('dispatched', models.BooleanField(default=False)),
                ('deadline', models.DateField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('sku', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('price', models.IntegerField(default=0)),
                ('used_by', models.IntegerField()),
                ('duration', models.DecimalField(decimal_places=2, max_digits=6)),
                ('batch', models.IntegerField()),
                ('production_time', models.IntegerField()),
                ('productors', models.CharField(max_length=100)),
                ('ingredients', models.ManyToManyField(related_name='ingredientes', through='bodega.Ingredient', to='bodega.Product')),
            ],
        ),
        migrations.AddField(
            model_name='ingredient',
            name='sku_ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sku_ingredient', to='bodega.Product'),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='sku_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sku_product', to='bodega.Product'),
        ),
    ]
