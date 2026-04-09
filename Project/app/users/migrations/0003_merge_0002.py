from django.db import migrations


class Migration(migrations.Migration):
    """
    Merge de las dos migraciones 0002 que existian en paralelo:
    - 0002_alter_user_email_alter_user_options
    - 0002_create_groups
    """

    dependencies = [
        ('users', '0002_alter_user_email_alter_user_options'),
        ('users', '0002_create_groups'),
    ]

    operations = []
