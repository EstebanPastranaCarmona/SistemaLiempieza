from django.db import models
from django.utils import timezone


class Task(models.Model):
    # ── Estados ───────────────────────────────────────────────
    PENDING        = 'PENDING'
    IN_PROGRESS    = 'IN_PROGRESS'
    PENDING_REVIEW = 'PENDING_REVIEW'
    VALIDATED      = 'VALIDATED'
    STATUS_CHOICES = [
        (PENDING,        'Pendiente'),
        (IN_PROGRESS,    'En progreso'),
        (PENDING_REVIEW, 'Pendiente de revisión'),
        (VALIDATED,      'Validada'),
    ]

    title       = models.CharField(max_length=150, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descripción')
    client      = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT,
        related_name='tasks', verbose_name='Cliente'
    )
    location    = models.ForeignKey(
        'clients.ClientLocation', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tasks', verbose_name='Ubicación'
    )
    assigned_to = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='assigned_tasks', verbose_name='Asignado a'
    )
    created_by  = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='created_tasks', verbose_name='Creado por'
    )
    scheduled_date = models.DateField(verbose_name='Fecha programada')
    scheduled_time = models.TimeField(null=True, blank=True, verbose_name='Hora')
    status      = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default=PENDING, verbose_name='Estado'
    )
    notes       = models.TextField(blank=True, verbose_name='Observaciones')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    # Estados que indican que la tarea ya fue atendida (no se marcan como vencidas)
    COMPLETED_STATUSES = (PENDING_REVIEW, VALIDATED)

    def is_overdue(self):
        """True solo si la fecha ya pasó Y la tarea sigue sin ser completada ni validada."""
        if self.status in self.COMPLETED_STATUSES:
            return False
        return self.scheduled_date < timezone.now().date()

    def __str__(self):
        return f'{self.title} — {self.client.name} ({self.scheduled_date})'

    class Meta:
        verbose_name        = 'Tarea'
        verbose_name_plural = 'Tareas'
        ordering            = ['scheduled_date', 'scheduled_time']


class TaskMaterial(models.Model):
    """Materiales (lotes) asignados a una tarea."""
    task     = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='materials', verbose_name='Tarea')
    lot      = models.ForeignKey(
        'inventory.Lot', on_delete=models.PROTECT,
        related_name='task_materials', verbose_name='Lote'
    )
    quantity = models.IntegerField(verbose_name='Cantidad')

    def __str__(self):
        return f'{self.lot.product.name} x{self.quantity} → {self.task.title}'

    class Meta:
        verbose_name        = 'Material de tarea'
        verbose_name_plural = 'Materiales de tarea'
        unique_together     = ('task', 'lot')


class Evidence(models.Model):
    """Evidencia (imagen o video + nota) subida al completar una tarea."""
    task        = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='evidences', verbose_name='Tarea')
    file        = models.FileField(upload_to='evidences/', blank=True, null=True, verbose_name='Archivo')
    note        = models.TextField(blank=True, verbose_name='Nota')
    uploaded_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='evidences', verbose_name='Subido por'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def is_video(self):
        if self.file:
            name = self.file.name.lower()
            return name.endswith(('.mp4', '.webm', '.ogg', '.mov', '.avi'))
        return False

    def __str__(self):
        return f'Evidencia #{self.pk} — {self.task.title}'

    class Meta:
        verbose_name        = 'Evidencia'
        verbose_name_plural = 'Evidencias'
        ordering            = ['-uploaded_at']


class TaskReview(models.Model):
    """Validación del supervisor sobre una tarea pendiente de revisión."""
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    RESULT_CHOICES = [(APPROVED, 'Aprobada'), (REJECTED, 'Rechazada')]

    task        = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='review', verbose_name='Tarea')
    reviewed_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='reviews', verbose_name='Revisado por'
    )
    result      = models.CharField(max_length=10, choices=RESULT_CHOICES, verbose_name='Resultado')
    comment     = models.TextField(blank=True, verbose_name='Comentario')
    reviewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_result_display()} — {self.task.title}'

    class Meta:
        verbose_name        = 'Revisión'
        verbose_name_plural = 'Revisiones'
