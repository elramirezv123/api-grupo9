# Generated by Django 2.2 on 2019-05-25 04:16

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
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True, serialize=False, verbose_name='ID')),
                ('production_batch', models.IntegerField()),
                ('for_batch', models.DecimalField(decimal_places=2, max_digits=6)),
                ('volume_in_store', models.IntegerField())
            ],
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True, serialize=False, verbose_name='ID')),
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
                ('cost', models.IntegerField(default=0)),
                ('price', models.IntegerField(default=0)),
                ('used_by', models.IntegerField()),
                ('duration', models.DecimalField(decimal_places=2, max_digits=6)),
                ('batch', models.IntegerField()),
                ('production_time', models.IntegerField()),
                ('productors', models.CharField(max_length=100)),
                ('p_type', models.CharField(max_length=100)),
                ('ingredients', models.ManyToManyField(
                    related_name='ingredientes', through='bodega.Ingredient', to='bodega.Product')),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('processed', models.BooleanField(default=False)),
                ('attended', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True, serialize=False, verbose_name='ID')),
                ('caller', models.CharField(max_length=255, null=True, default=None)),
                ('comment', models.CharField(max_length=255, null=True, default=None)),
                ('created_at', models.DateTimeField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='ingredient',
            name='sku_ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='sku_ingredient', to='bodega.Product'),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='sku_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='sku_product', to='bodega.Product'),
        ),
    ]
