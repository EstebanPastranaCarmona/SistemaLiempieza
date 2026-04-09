# Generated migration for app.clients

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('contact_name', models.CharField(max_length=100, verbose_name='Contacto')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Teléfono')),
                ('email', models.EmailField(max_length=254, verbose_name='Correo')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ClientLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre de la ubicación')),
                ('address', models.CharField(max_length=200, verbose_name='Dirección')),
                ('notes', models.TextField(blank=True, verbose_name='Notas')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activa')),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='locations',
                    to='clients.client',
                    verbose_name='Cliente',
                )),
            ],
            options={
                'verbose_name': 'Ubicación',
                'verbose_name_plural': 'Ubicaciones',
                'ordering': ['client', 'name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='clientlocation',
            unique_together={('client', 'name')},
        ),
    ]
