from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from app.inventory.models import Product, Lot, Movement
from app.tasks.models import Task
from app.clients.models import Client


def _supervisor_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not (request.user.is_admin or request.user.is_supervisor):
            messages.error(request, 'Solo supervisores y administradores pueden ver los reportes.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


@login_required
@_supervisor_required
def report_inventory(request):
    """Reporte de inventario: stock, lotes o movimientos."""
    tipo      = request.GET.get('tipo', '')       # stock | lotes | movimientos
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    headers   = []
    rows      = []

    if tipo == 'stock':
        headers = ['Producto', 'Tipo', 'Unidad', 'Stock actual', 'Stock mínimo', 'Estado']
        for p in Product.objects.filter(is_active=True).order_by('name'):
            stock  = p.get_total_stock()
            estado = 'Bajo' if stock < p.min_stock else 'OK'
            rows.append([p.name, p.product_type, p.unit, stock, p.min_stock, estado])

    elif tipo == 'lotes':
        headers = ['Producto', 'Lote #', 'Cantidad', 'Vencimiento', 'Estado']
        for lot in Lot.objects.filter(is_active=True).select_related('product').order_by('expiration_date'):
            if lot.is_expired():
                estado = 'Vencido'
            elif lot.days_until_expiration() <= 7:
                estado = 'Por vencer'
            else:
                estado = 'Vigente'
            rows.append([
                lot.product.name, lot.pk,
                f'{lot.quantity} {lot.product.unit}',
                lot.expiration_date.strftime('%d/%m/%Y'),
                estado,
            ])

    elif tipo == 'movimientos':
        headers = ['Fecha', 'Producto', 'Lote #', 'Tipo', 'Cantidad', 'Motivo']
        qs = Movement.objects.select_related('lot__product').order_by('-date')
        if date_from:
            qs = qs.filter(date__date__gte=date_from)
        if date_to:
            qs = qs.filter(date__date__lte=date_to)
        for m in qs:
            rows.append([
                m.date.strftime('%d/%m/%Y %H:%M'),
                m.lot.product.name,
                m.lot.pk,
                m.get_movement_type_display(),
                f'{m.quantity} {m.lot.product.unit}',
                m.reason or '—',
            ])

    return render(request, 'reports/inventory.html', {
        'tipo': tipo, 'date_from': date_from, 'date_to': date_to,
        'headers': headers, 'rows': rows,
    })


@login_required
@_supervisor_required
def report_tasks(request):
    """Reporte de tareas: general, vencidas o resumen por cliente."""
    tipo      = request.GET.get('tipo', '')       # general | vencidas | por_cliente
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    client_id = request.GET.get('client', '')
    today     = timezone.now().date()
    clients   = Client.objects.filter(is_active=True).order_by('name')
    headers   = []
    rows      = []

    if tipo == 'general':
        headers = ['Tarea', 'Cliente', 'Fecha programada', 'Estado', 'Asignado a']
        qs = Task.objects.select_related('client', 'assigned_to').order_by('-scheduled_date')
        if client_id:
            qs = qs.filter(client_id=client_id)
        if date_from:
            qs = qs.filter(scheduled_date__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_date__lte=date_to)
        for t in qs:
            rows.append([
                t.title, t.client.name,
                t.scheduled_date.strftime('%d/%m/%Y'),
                t.get_status_display(),
                t.assigned_to.get_full_name() if t.assigned_to else '—',
            ])

    elif tipo == 'vencidas':
        headers = ['Tarea', 'Cliente', 'Fecha programada', 'Estado', 'Asignado a']
        qs = Task.objects.filter(
            status__in=[Task.PENDING, Task.IN_PROGRESS],
            scheduled_date__lt=today,
        ).select_related('client', 'assigned_to').order_by('scheduled_date')
        if client_id:
            qs = qs.filter(client_id=client_id)
        for t in qs:
            rows.append([
                t.title, t.client.name,
                t.scheduled_date.strftime('%d/%m/%Y'),
                t.get_status_display(),
                t.assigned_to.get_full_name() if t.assigned_to else '—',
            ])

    elif tipo == 'por_cliente':
        headers = ['Cliente', 'Pendientes', 'En progreso', 'Por revisar', 'Validadas', 'Total']
        for c in clients:
            qs = Task.objects.filter(client=c)
            rows.append([
                c.name,
                qs.filter(status=Task.PENDING).count(),
                qs.filter(status=Task.IN_PROGRESS).count(),
                qs.filter(status=Task.PENDING_REVIEW).count(),
                qs.filter(status=Task.VALIDATED).count(),
                qs.count(),
            ])

    return render(request, 'reports/tasks.html', {
        'tipo': tipo, 'date_from': date_from, 'date_to': date_to,
        'client_id': client_id, 'clients': clients,
        'headers': headers, 'rows': rows,
    })
