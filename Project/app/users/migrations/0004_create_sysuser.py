from django.db import migrations
from django.contrib.auth.hashers import make_password
import uuid


def create_sysuser(apps, schema_editor):
    User = apps.get_model('users', 'User')
    Group = apps.get_model('auth', 'Group')

    # Crear superusuario solo si no existe
    if not User.objects.filter(username='sysuser').exists():
        user = User.objects.create(
            id=uuid.uuid4(),
            username='sysuser',
            email='',
            password=make_password('123'),
            is_superuser=True,
            is_staff=True,
            is_active=True,
            first_name='System',
            last_name='Admin',
        )
        # Agregar al grupo Administrador si existe
        try:
            admin_group = Group.objects.get(name='Administrador')
            user.groups.add(admin_group)
        except Group.DoesNotExist:
            pass


def delete_sysuser(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(username='sysuser').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_merge_0002'),
    ]

    operations = [
        migrations.RunPython(create_sysuser, delete_sysuser),
    ]
