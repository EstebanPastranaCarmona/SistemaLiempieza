# Generated migration for app.inventory

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
                ('product_type', models.CharField(max_length=60, verbose_name='Tipo')),
                ('unit', models.CharField(max_length=30, verbose_name='Unidad de medida')),
                ('min_stock', models.IntegerField(default=0, verbose_name='Stock mínimo')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Lot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(verbose_name='Cantidad')),
                ('expiration_date', models.DateField(verbose_name='Fecha de vencimiento')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='lots',
                    to='inventory.product',
                    verbose_name='Producto',
                )),
            ],
            options={
                'verbose_name': 'Lote',
                'verbose_name_plural': 'Lotes',
                'ordering': ['expiration_date'],
            },
        ),
        migrations.CreateModel(
            name='Movement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(
                    choices=[('INSIDE', 'Entrada'), ('OUTSIDE', 'Salida')],
                    max_length=10,
                    verbose_name='Tipo',
                )),
                ('quantity', models.IntegerField(verbose_name='Cantidad')),
                ('reason', models.CharField(max_length=200, verbose_name='Motivo')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('lot', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='movements',
                    to='inventory.lot',
                    verbose_name='Lote',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='movements',
                    to='users.user',
                    verbose_name='Registrado por',
                )),
            ],
            options={
                'verbose_name': 'Movimiento',
                'verbose_name_plural': 'Movimientos',
                'ordering': ['-date'],
            },
        ),
    ]
