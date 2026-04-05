from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Task, TaskMaterial, Evidence, TaskReview
from .forms import TaskForm, TaskMaterialForm, EvidenceForm, TaskReviewForm, TaskCompleteForm
from app.users.views import admin_required


def supervisor_or_admin_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not (request.user.is_admin or request.user.is_supervisor):
            messages.error(request, 'No tenés permisos para acceder a esta sección.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Lista de tareas ──────────────────────────────────────────

@login_required
def task_list(request):
    user   = request.user
    status = request.GET.get('status', '')

    if user.is_operario:
        tasks = Task.objects.filter(assigned_to=user).select_related('client', 'location', 'assigned_to')
    else:
        tasks = Task.objects.all().select_related('client', 'location', 'assigned_to')

    if status:
        # Filtro explícito: mostrar lo que el usuario pidió
        tasks = tasks.filter(status=status)
    else:
        # Por defecto: ocultar las validadas
        tasks = tasks.exclude(status=Task.VALIDATED)

    tasks = tasks.order_by('scheduled_date', 'scheduled_time')
    today = timezone.now().date()

    return render(request, 'tasks/task_list.html', {
        'tasks':          tasks,
        'today':          today,
        'status':         status,
        'status_choices': Task.STATUS_CHOICES,
    })


# ── Detalle de tarea ─────────────────────────────────────────

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.user.is_operario and task.assigned_to != request.user:
        messages.error(request, 'No tenés acceso a esta tarea.')
        return redirect('tasks:task_list')
    return render(request, 'tasks/task_detail.html', {'task': task})


# ── Crear / Editar tarea ─────────────────────────────────────

@login_required
@supervisor_or_admin_required
def task_create(request):
    form = TaskForm(request.POST or None)
    if form.is_valid():
        task            = form.save(commit=False)
        task.created_by = request.user
        task.save()
        messages.success(request, f'Tarea "{task.title}" creada correctamente.')
        return redirect('tasks:task_detail', pk=task.pk)
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Nueva'})


@login_required
@supervisor_or_admin_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, f'Tarea "{task.title}" actualizada.')
        return redirect('tasks:task_detail', pk=task.pk)
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Editar', 'task': task})


# ── Iniciar tarea (SOLO el operario asignado) ────────────────

@login_required
@require_POST
def task_start(request, pk):
    task = get_object_or_404(Task, pk=pk)
    # Solo el operario asignado puede iniciar la tarea
    if task.assigned_to != request.user:
        messages.error(request, 'Solo el operario asignado puede iniciar esta tarea.')
        return redirect('tasks:task_detail', pk=pk)
    if task.status != Task.PENDING:
        messages.info(request, 'La tarea no está en estado Pendiente.')
        return redirect('tasks:task_detail', pk=pk)
    task.status = Task.IN_PROGRESS
    task.save()
    messages.success(request, 'Tarea iniciada. Ahora está En progreso.')
    return redirect('tasks:task_detail', pk=pk)


# ── Enviar a revisión (operario asignado) ────────────────────

@login_required
def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.user.is_operario and task.assigned_to != request.user:
        messages.error(request, 'No podés completar esta tarea.')
        return redirect('tasks:task_list')
    if task.status not in (Task.PENDING, Task.IN_PROGRESS):
        messages.info(request, 'Esta tarea no puede enviarse a revisión en su estado actual.')
        return redirect('tasks:task_detail', pk=pk)
    if not task.evidences.exists():
        messages.error(request, 'Debés subir al menos una evidencia antes de enviar la tarea a revisión.')
        return redirect('tasks:task_detail', pk=pk)

    form = TaskCompleteForm(request.POST or None, instance=task)
    if form.is_valid():
        task.status = Task.PENDING_REVIEW
        form.save()
        messages.success(request, 'Tarea enviada a revisión del supervisor.')
        return redirect('tasks:task_detail', pk=pk)
    return render(request, 'tasks/task_complete.html', {'form': form, 'task': task})


# ── Evidencias ───────────────────────────────────────────────

@login_required
def evidence_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if request.user.is_operario and task.assigned_to != request.user:
        messages.error(request, 'No podés subir evidencia para esta tarea.')
        return redirect('tasks:task_list')

    form = EvidenceForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        evidence             = form.save(commit=False)
        evidence.task        = task
        evidence.uploaded_by = request.user
        evidence.save()
        messages.success(request, 'Evidencia subida correctamente.')
        return redirect('tasks:task_detail', pk=task_pk)
    return render(request, 'tasks/evidence_form.html', {'form': form, 'task': task})


# ── Materiales ───────────────────────────────────────────────

@login_required
@supervisor_or_admin_required
def task_material_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    form = TaskMaterialForm(request.POST or None)
    if form.is_valid():
        material      = form.save(commit=False)
        material.task = task
        if material.lot.quantity < material.quantity:
            messages.error(request, f'Stock insuficiente en el lote seleccionado (disponible: {material.lot.quantity}).')
        else:
            from app.inventory.models import Movement
            material.lot.quantity -= material.quantity
            material.lot.save()
            Movement.objects.create(
                movement_type=Movement.OUTSIDE,
                lot=material.lot,
                quantity=material.quantity,
                reason=f'Consumo en tarea: {task.title}',
                created_by=request.user,
            )
            material.save()
            messages.success(request, 'Material asignado y descontado del inventario.')
            return redirect('tasks:task_detail', pk=task_pk)
    return render(request, 'tasks/task_material_form.html', {'form': form, 'task': task})


@login_required
@supervisor_or_admin_required
@require_POST
def task_material_delete(request, pk):
    material = get_object_or_404(TaskMaterial, pk=pk)
    task_pk  = material.task.pk
    material.delete()
    messages.success(request, 'Material eliminado de la tarea.')
    return redirect('tasks:task_detail', pk=task_pk)


# ── Revisión del supervisor ──────────────────────────────────

@login_required
@supervisor_or_admin_required
def task_review(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if task.status != Task.PENDING_REVIEW:
        messages.error(request, 'Solo se pueden revisar tareas con estado Pendiente de revisión.')
        return redirect('tasks:task_detail', pk=task_pk)
    if hasattr(task, 'review'):
        task.review.delete()

    form = TaskReviewForm(request.POST or None)
    if form.is_valid():
        review             = form.save(commit=False)
        review.task        = task
        review.reviewed_by = request.user
        review.save()
        if review.result == TaskReview.APPROVED:
            task.status = Task.VALIDATED
            task.save()
            messages.success(request, 'Tarea aprobada y marcada como Validada.')
        else:
            task.status = Task.PENDING
            task.save()
            messages.warning(request, 'Tarea rechazada. El operario debe completarla nuevamente.')
        return redirect('tasks:task_detail', pk=task_pk)
    return render(request, 'tasks/task_review.html', {'form': form, 'task': task})
