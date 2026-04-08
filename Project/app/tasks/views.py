from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Task, TaskMaterial, Evidence, TaskReview
from .forms import TaskForm, TaskMaterialForm, TaskMaterialUsedForm, EvidenceForm, TaskReviewForm, TaskCompleteForm
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


# ── Lista de tareas ───────────────────────────────────────────────

@login_required
def task_list(request):
    user   = request.user
    status = request.GET.get('status', '')

    if user.is_operario:
        tasks = Task.objects.filter(assigned_to=user).select_related('client', 'location', 'assigned_to')
    else:
        tasks = Task.objects.all().select_related('client', 'location', 'assigned_to')

    if status:
        tasks = tasks.filter(status=status)
    else:
        tasks = tasks.exclude(status=Task.VALIDATED)

    tasks = tasks.order_by('scheduled_date', 'scheduled_time')
    today = timezone.now().date()

    return render(request, 'tasks/task_list.html', {
        'tasks':          tasks,
        'today':          today,
        'status':         status,
        'status_choices': Task.STATUS_CHOICES,
    })


# ── Detalle de tarea ───────────────────────────────────────────────

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.user.is_operario and task.assigned_to != request.user:
        messages.error(request, 'No tenés acceso a esta tarea.')
        return redirect('tasks:task_list')
    return render(request, 'tasks/task_detail.html', {'task': task})


# ── Crear / Editar tarea ─────────────────────────────────────────────

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
    if task.status == Task.VALIDATED:
        messages.error(request, 'No se puede editar una tarea ya validada.')
        return redirect('tasks:task_detail', pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, f'Tarea "{task.title}" actualizada.')
        return redirect('tasks:task_detail', pk=task.pk)
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Editar', 'task': task})


# ── Iniciar tarea (SOLO el operario asignado) ────────────────────────

@login_required
@require_POST
def task_start(request, pk):
    task = get_object_or_404(Task, pk=pk)
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


# ── Enviar a revisión (operario asignado) ──────────────────────────

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
        return redirect('tasks:task_detail', pk=task.pk)
    return render(request, 'tasks/task_complete.html', {'form': form, 'task': task})


# ── Evidencias ─────────────────────────────────────────────────────

@login_required
def evidence_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if request.user.is_operario and task.assigned_to != request.user:
        messages.error(request, 'No podés subir evidencia para esta tarea.')
        return redirect('tasks:task_list')
    if task.status == Task.VALIDATED:
        messages.error(request, 'No se puede subir evidencia a una tarea ya validada.')
        return redirect('tasks:task_detail', pk=task_pk)

    form = EvidenceForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        evidence             = form.save(commit=False)
        evidence.task        = task
        evidence.uploaded_by = request.user
        evidence.save()
        messages.success(request, 'Evidencia subida correctamente.')
        return redirect('tasks:task_detail', pk=task_pk)
    return render(request, 'tasks/evidence_form.html', {'form': form, 'task': task})


# ── Materiales ──────────────────────────────────────────────────
# CU6: operarios y supervisores pueden agregar materiales

@login_required
def task_material_create(request, task_pk):
    from app.inventory.models import Lot
    task = get_object_or_404(Task, pk=task_pk)

    # Bloqueo total en VALIDATED
    if task.status == Task.VALIDATED:
        messages.error(request, 'No se pueden agregar materiales a una tarea ya validada.')
        return redirect('tasks:task_detail', pk=task_pk)

    # Operarios solo pueden agregar materiales a sus propias tareas activas
    if request.user.is_operario:
        if task.assigned_to != request.user:
            messages.error(request, 'Solo podés agregar materiales a tus propias tareas.')
            return redirect('tasks:task_list')
        if task.status not in (Task.PENDING, Task.IN_PROGRESS):
            messages.error(request, 'Solo podés agregar materiales a tareas pendientes o en progreso.')
            return redirect('tasks:task_detail', pk=task_pk)

    lot_stock_data = Lot.objects.filter(is_active=True).select_related('product').values_list(
        'id', 'quantity', 'product__unit'
    )

    form = TaskMaterialForm(request.POST or None)
    if form.is_valid():
        material      = form.save(commit=False)
        material.task = task
        if material.lot.quantity < material.quantity:
            messages.error(request, f'Stock insuficiente en el lote seleccionado (disponible: {material.lot.quantity} {material.lot.product.unit}).')
        else:
            if TaskMaterial.objects.filter(task=task, lot=material.lot).exists():
                messages.error(request, 'Ese lote ya fue asignado a esta tarea. Editá la cantidad existente o elegí otro lote.')
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

    return render(request, 'tasks/task_material_form.html', {
        'form':           form,
        'task':           task,
        'lot_stock_data': lot_stock_data,
    })


@login_required
@supervisor_or_admin_required
@require_POST
def task_material_delete(request, pk):
    from app.inventory.models import Movement
    material = get_object_or_404(TaskMaterial, pk=pk)
    task     = material.task
    task_pk  = task.pk

    if task.status == Task.VALIDATED:
        messages.error(request, 'No se pueden eliminar materiales de una tarea ya validada.')
        return redirect('tasks:task_detail', pk=task_pk)

    lot = material.lot

    # Si ya se reportó uso real, devolvemos solo el sobrante (lo que no se usó).
    # Si nunca se reportó uso (quantity_used es None), devolvemos la cantidad
    # completa asignada porque el stock fue descontado al asignar el material.
    if material.quantity_used is not None:
        devolucion = material.quantity - material.quantity_used
    else:
        devolucion = material.quantity

    if devolucion > 0:
        lot.quantity += devolucion
        lot.save()
        Movement.objects.create(
            movement_type=Movement.INSIDE,
            lot=lot,
            quantity=devolucion,
            reason=f'Devolución por desasignación de material en tarea: {task.title}',
            created_by=request.user,
        )
        messages.success(request, f'Material eliminado. {devolucion} {lot.product.unit} devueltos al lote.')
    else:
        messages.success(request, 'Material eliminado. Sin stock a devolver (todo fue consumido).')

    material.delete()
    return redirect('tasks:task_detail', pk=task_pk)


# ── Reportar uso real de material — SOLO operario asignado ─────────

@login_required
def task_material_set_used(request, pk):
    """
    Solo el operario asignado a la tarea puede reportar el uso real de un material.
    Admins y supervisores NO tienen acceso a esta vista (ellos gestionan el inventario
    directamente, no el consumo operativo).
    """
    from app.inventory.models import Movement
    material = get_object_or_404(TaskMaterial, pk=pk)
    task     = material.task

    # Solo el operario asignado puede reportar uso
    if task.assigned_to != request.user:
        messages.error(request, 'Solo el operario asignado puede reportar el uso de materiales.')
        return redirect('tasks:task_detail', pk=task.pk)

    # Bloqueo total en VALIDATED
    if task.status == Task.VALIDATED:
        messages.error(request, 'La tarea ya está validada, no se puede modificar el uso de materiales.')
        return redirect('tasks:task_detail', pk=task.pk)

    prev_used = material.quantity_used

    # Precargamos el input con la cantidad asignada si no hay reporte previo
    initial = {}
    if prev_used is None:
        initial['quantity_used'] = material.quantity

    form = TaskMaterialUsedForm(request.POST or None, instance=material, initial=initial)
    if form.is_valid():
        new_used = form.cleaned_data['quantity_used']

        if prev_used is None:
            sobrante = material.quantity - new_used
        else:
            sobrante = prev_used - new_used

        lot = material.lot
        if sobrante > 0:
            lot.quantity += sobrante
            lot.save()
            Movement.objects.create(
                movement_type=Movement.INSIDE,
                lot=lot,
                quantity=sobrante,
                reason=f'Devolución de sobrante al reportar uso real en tarea: {task.title}',
                created_by=request.user,
            )
        elif sobrante < 0:
            extra = abs(sobrante)
            if lot.quantity < extra:
                messages.error(request, f'No hay suficiente stock en el lote para registrar ese consumo adicional (disponible: {lot.quantity} {lot.product.unit}).')
                return render(request, 'tasks/task_material_used_form.html', {'form': form, 'material': material, 'task': task})
            lot.quantity -= extra
            lot.save()
            Movement.objects.create(
                movement_type=Movement.OUTSIDE,
                lot=lot,
                quantity=extra,
                reason=f'Consumo adicional ajustado al reportar uso real en tarea: {task.title}',
                created_by=request.user,
            )

        form.save()
        messages.success(request, f'Uso reportado: {new_used} {lot.product.unit} de {lot.product.name}.')
        return redirect('tasks:task_detail', pk=task.pk)

    return render(request, 'tasks/task_material_used_form.html', {
        'form':     form,
        'material': material,
        'task':     task,
    })


# ── Revisión del supervisor (CU7) ──────────────────────────────────────────

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
            task.status = Task.IN_PROGRESS
            task.save()
            operario_name = ''
            if task.assigned_to:
                operario_name = task.assigned_to.get_full_name() or task.assigned_to.username
            comentario = review.comment or 'Sin comentario del supervisor.'
            messages.warning(
                request,
                f'Tarea rechazada. {operario_name} verá el motivo al ingresar: "{comentario}". '
                f'La tarea volvió a estado En progreso.'
            )
        return redirect('tasks:task_detail', pk=task_pk)
    return render(request, 'tasks/task_review.html', {'form': form, 'task': task})
