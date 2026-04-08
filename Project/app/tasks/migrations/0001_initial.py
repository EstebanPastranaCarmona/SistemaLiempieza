from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0001_initial'),
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, verbose_name='T\u00edtulo')),
                ('description', models.TextField(blank=True, verbose_name='Descripci\u00f3n')),
                ('scheduled_date', models.DateField(verbose_name='Fecha programada')),
                ('scheduled_time', models.TimeField(blank=True, null=True, verbose_name='Hora')),
                ('status', models.CharField(
                    choices=[
                        ('PENDING', 'Pendiente'),
                        ('IN_PROGRESS', 'En progreso'),
                        ('COMPLETED', 'Completada'),
                        ('VALIDATED', 'Validada'),
                    ],
                    default='PENDING',
                    max_length=20,
                    verbose_name='Estado',
                )),
                ('notes', models.TextField(blank=True, verbose_name='Observaciones')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='tasks',
                    to='clients.client',
                    verbose_name='Cliente',
                )),
                ('location', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tasks',
                    to='clients.clientlocation',
                    verbose_name='Ubicaci\u00f3n',
                )),
                ('assigned_to', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_tasks',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Asignado a',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_tasks',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Creado por',
                )),
            ],
            options={
                'verbose_name': 'Tarea',
                'verbose_name_plural': 'Tareas',
                'ordering': ['scheduled_date', 'scheduled_time'],
            },
        ),
        migrations.CreateModel(
            name='TaskMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(verbose_name='Cantidad')),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='materials',
                    to='tasks.task',
                    verbose_name='Tarea',
                )),
                ('lot', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='task_materials',
                    to='inventory.lot',
                    verbose_name='Lote',
                )),
            ],
            options={
                'verbose_name': 'Material de tarea',
                'verbose_name_plural': 'Materiales de tarea',
                'unique_together': {('task', 'lot')},
            },
        ),
        migrations.CreateModel(
            name='Evidence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='evidences/', verbose_name='Imagen')),
                ('note', models.TextField(blank=True, verbose_name='Nota')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evidences',
                    to='tasks.task',
                    verbose_name='Tarea',
                )),
                ('uploaded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='evidences',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Subido por',
                )),
            ],
            options={
                'verbose_name': 'Evidencia',
                'verbose_name_plural': 'Evidencias',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.CharField(
                    choices=[('APPROVED', 'Aprobada'), ('REJECTED', 'Rechazada')],
                    max_length=10,
                    verbose_name='Resultado',
                )),
                ('comment', models.TextField(blank=True, verbose_name='Comentario')),
                ('reviewed_at', models.DateTimeField(auto_now_add=True)),
                ('task', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='review',
                    to='tasks.task',
                    verbose_name='Tarea',
                )),
                ('reviewed_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviews',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Revisado por',
                )),
            ],
            options={
                'verbose_name': 'Revisi\u00f3n',
                'verbose_name_plural': 'Revisiones',
            },
        ),
    ]
