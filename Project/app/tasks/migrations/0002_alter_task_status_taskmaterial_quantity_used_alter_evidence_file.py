from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        # Cambiar choices del campo status en Task
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pendiente'),
                    ('IN_PROGRESS', 'En progreso'),
                    ('PENDING_REVIEW', 'Pendiente de revisión'),
                    ('VALIDATED', 'Validada'),
                ],
                default='PENDING',
                max_length=20,
                verbose_name='Estado',
            ),
        ),
        # Agregar quantity_used a TaskMaterial
        migrations.AddField(
            model_name='taskmaterial',
            name='quantity_used',
            field=models.IntegerField(
                null=True,
                blank=True,
                verbose_name='Cantidad usada',
                help_text='Cantidad real utilizada en la tarea.',
            ),
        ),
        # Renombrar image -> file en Evidence (eliminar y agregar)
        migrations.RemoveField(
            model_name='evidence',
            name='image',
        ),
        migrations.AddField(
            model_name='evidence',
            name='file',
            field=models.FileField(
                upload_to='evidences/',
                blank=True,
                null=True,
                verbose_name='Archivo',
            ),
        ),
        # Actualizar verbose_name de quantity en TaskMaterial
        migrations.AlterField(
            model_name='taskmaterial',
            name='quantity',
            field=models.IntegerField(verbose_name='Cantidad asignada'),
        ),
    ]
