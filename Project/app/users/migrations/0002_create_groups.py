from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for nombre in ['Administrador', 'Supervisor', 'Operario']:
        Group.objects.get_or_create(name=nombre)


def reverse_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Administrador', 'Supervisor', 'Operario']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  
    ]

    operations = [
        migrations.RunPython(create_groups, reverse_groups),
    ]
