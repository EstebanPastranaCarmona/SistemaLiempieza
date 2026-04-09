from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(unique=True, blank=True, verbose_name='email address'),
        ),
        migrations.AlterModelOptions(
            name='user',
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
            },
        ),
        migrations.AlterUniqueTogether(
            name='user',
            unique_together={('username', 'email')},
        ),
    ]
