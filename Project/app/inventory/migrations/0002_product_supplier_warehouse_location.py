from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='supplier',
            field=models.CharField(blank=True, max_length=150, verbose_name='Proveedor'),
        ),
        migrations.AddField(
            model_name='product',
            name='warehouse_location',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ubicación en almacén'),
        ),
    ]
