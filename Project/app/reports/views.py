from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from app.inventory.models import Product, Lot, Movement
from app.tasks.models import Task
from app.clients.models import Client


def _require_supervisor(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_admin or request.user.is_supervisor):
            messages.error(request, 'Solo supervisores y administradores pueden ver los reportes.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────
# Dashboard principal de reportes
# ─────────────────────────────────────────────────────────────────
@login_required
@_require_supervisor
def reports_dashboard(request):
    today = timezone.now().date()

    # Inventario — conteos simples
    total_products = Product.objects.filter(is_active=True).count()

    low_stock_products = [
        p for p in Product.objects.filter(is_active=True)
        if p.is_below_min_stock()
    ]

    expiring_lots = Lot.objects.filter(
        is_active=True,
        expiration_date__gte=today,
        expiration_date__lte=today + timedelta(days=7),
    ).select_related('product')

    expired_lots = Lot.objects.filter(
        is_active=True,
        expiration_date__lt=today,
    ).select_related('product')

    # Tareas — todos los estados sin filtro de fecha
    all_tasks = Task.objects.all()
    tasks_pending   = all_tasks.filter(status=Task.PENDING).count()
    tasks_progress  = all_tasks.filter(status=Task.IN_PROGRESS).count()
    tasks_review    = all_tasks.filter(status=Task.PENDING_REVIEW).count()
    tasks_validated = all_tasks.filter(status=Task.VALIDATED).count()
    tasks_overdue   = all_tasks.filter(
        status__in=[Task.PENDING, Task.IN_PROGRESS],
        scheduled_date__lt=today,
    ).count()

    return render(request, 'reports/dashboard.html', {
        'today': today,
        'total_products':      total_products,
        'low_stock_count':     len(low_stock_products),
        'expiring_soon_count': expiring_lots.count(),
        'expired_count':       expired_lots.count(),
        'tasks_pending':   tasks_pending,
        'tasks_progress':  tasks_progress,
        'tasks_review':    tasks_review,
        'tasks_validated': tasks_validated,
        'tasks_overdue':   tasks_overdue,
    })


# ─────────────────────────────────────────────────────────────────
# Reporte de inventario — todos los productos activos con su estado
# ─────────────────────────────────────────────────────────────────
@login_required
@_require_supervisor
def report_inventory(request):
    today    = timezone.now().date()
    products = Product.objects.filter(is_active=True).order_by('name')

    rows = []
    for p in products:
        active_lots   = Lot.objects.filter(product=p, is_active=True)
        total_stock   = sum(l.quantity for l in active_lots)
        expired_count = active_lots.filter(expiration_date__lt=today).count()
        expiring_count = active_lots.filter(
            expiration_date__gte=today,
            expiration_date__lte=today + timedelta(days=7),
        ).count()
        is_low = total_stock < p.min_stock
        rows.append({
            'product':       p,
            'total_stock':   total_stock,
            'is_low':        is_low,
            'expired_lots':  expired_count,
            'expiring_lots': expiring_count,
            'lot_count':     active_lots.count(),
        })

    return render(request, 'reports/inventory.html', {
        'rows':  rows,
        'today': today,
    })


# ─────────────────────────────────────────────────────────────────
# Reporte de tareas — con filtros opcionales
# ─────────────────────────────────────────────────────────────────
@login_required
@_require_supervisor
def report_tasks(request):
    today     = timezone.now().date()
    status_f  = request.GET.get('status', '')
    client_id = request.GET.get('client', '')

    tasks = Task.objects.select_related('client', 'assigned_to').order_by('-scheduled_date')

    if status_f:
        tasks = tasks.filter(status=status_f)
    if client_id:
        tasks = tasks.filter(client_id=client_id)

    clients = Client.objects.filter(is_active=True).order_by('name')

    return render(request, 'reports/tasks.html', {
        'tasks':          tasks,
        'clients':        clients,
        'status_f':       status_f,
        'client_id':      client_id,
        'status_choices': Task.STATUS_CHOICES,
        'today':          today,
    })


# ─────────────────────────────────────────────────────────────────
# Reporte de alertas — stock bajo + lotes vencidos/por vencer
# ─────────────────────────────────────────────────────────────────
@login_required
@_require_supervisor
def report_alerts(request):
    today = timezone.now().date()

    # Productos con stock bajo (comparando contra min_stock)
    low_products = [
        p for p in Product.objects.filter(is_active=True).order_by('name')
        if sum(l.quantity for l in Lot.objects.filter(product=p, is_active=True)) < p.min_stock
    ]

    expiring_lots = Lot.objects.filter(
        is_active=True,
        expiration_date__gte=today,
        expiration_date__lte=today + timedelta(days=7),
    ).select_related('product').order_by('expiration_date')

    expired_lots = Lot.objects.filter(
        is_active=True,
        expiration_date__lt=today,
    ).select_related('product').order_by('expiration_date')

    return render(request, 'reports/alerts.html', {
        'low_products':   low_products,
        'expiring_lots':  expiring_lots,
        'expired_lots':   expired_lots,
        'today':          today,
    })


# ─────────────────────────────────────────────────────────────────
# Reporte de consumo de materiales por periodo
# ─────────────────────────────────────────────────────────────────
@login_required
@_require_supervisor
def report_consumption(request):
    today     = timezone.now().date()
    date_from = request.GET.get('date_from', str(today.replace(day=1)))
    date_to   = request.GET.get('date_to',   str(today))

    movements = Movement.objects.filter(
        movement_type=Movement.OUTSIDE,
        date__date__range=[date_from, date_to],
    ).select_related('lot__product').order_by('-date')

    return render(request, 'reports/consumption.html', {
        'movements': movements,
        'date_from': date_from,
        'date_to':   date_to,
        'today':     today,
    })


# ─────────────────────────────────────────────────────────────────
# Reporte por cliente — tareas realizadas
# ─────────────────────────────────────────────────────────────────
@login_required
@_require_supervisor
def report_clients(request):
    today     = timezone.now().date()
    client_id = request.GET.get('client', '')

    clients = Client.objects.filter(is_active=True).order_by('name')
    tasks   = Task.objects.select_related('client', 'assigned_to').order_by('-scheduled_date')

    if client_id:
        tasks = tasks.filter(client_id=client_id)

    return render(request, 'reports/clients.html', {
        'tasks':     tasks,
        'clients':   clients,
        'client_id': client_id,
        'today':     today,
    })
