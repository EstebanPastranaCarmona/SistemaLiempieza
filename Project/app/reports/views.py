from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date, timedelta

from app.inventory.models import Product, Lot, Movement
from app.tasks.models import Task, TaskMaterial
from app.clients.models import Client


def _supervisor_or_admin(request):
    return request.user.is_authenticated and (
        request.user.is_admin or request.user.is_supervisor
    )


def _require_supervisor(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _supervisor_or_admin(request):
            messages.error(request, 'Solo supervisores y administradores pueden ver los reportes.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@_require_supervisor
def reports_dashboard(request):
    today = timezone.now().date()

    total_products  = Product.objects.filter(is_active=True).count()
    low_stock_count = sum(1 for p in Product.objects.filter(is_active=True) if p.is_below_min_stock())
    expiring_soon   = Lot.objects.filter(
        is_active=True,
        expiration_date__range=[today, today + timedelta(days=7)]
    ).count()
    expired_count   = Lot.objects.filter(is_active=True, expiration_date__lt=today).count()

    tasks_pending   = Task.objects.filter(status=Task.PENDING).count()
    tasks_progress  = Task.objects.filter(status=Task.IN_PROGRESS).count()
    tasks_review    = Task.objects.filter(status=Task.PENDING_REVIEW).count()
    tasks_validated = Task.objects.filter(status=Task.VALIDATED).count()
    tasks_overdue   = sum(1 for t in Task.objects.filter(
        status__in=[Task.PENDING, Task.IN_PROGRESS]
    ) if t.is_overdue())

    start_month     = today.replace(day=1)
    movements_month = Movement.objects.filter(date__date__gte=start_month)
    entries_month   = movements_month.filter(movement_type=Movement.INSIDE).aggregate(t=Sum('quantity'))['t'] or 0
    exits_month     = movements_month.filter(movement_type=Movement.OUTSIDE).aggregate(t=Sum('quantity'))['t'] or 0

    return render(request, 'reports/dashboard.html', {
        'total_products':  total_products,
        'low_stock_count': low_stock_count,
        'expiring_soon':   expiring_soon,
        'expired_count':   expired_count,
        'tasks_pending':   tasks_pending,
        'tasks_progress':  tasks_progress,
        'tasks_review':    tasks_review,
        'tasks_validated': tasks_validated,
        'tasks_overdue':   tasks_overdue,
        'entries_month':   entries_month,
        'exits_month':     exits_month,
        'today':           today,
    })


@login_required
@_require_supervisor
def report_inventory(request):
    today    = timezone.now().date()
    products = Product.objects.filter(is_active=True).prefetch_related('lots')

    filter_status = request.GET.get('status', '')
    if filter_status == 'low':
        products = [p for p in products if p.is_below_min_stock()]
    elif filter_status == 'expiring':
        ids = Lot.objects.filter(
            is_active=True,
            expiration_date__range=[today, today + timedelta(days=7)]
        ).values_list('product_id', flat=True)
        products = [p for p in products if p.id in list(ids)]
    elif filter_status == 'expired':
        ids = Lot.objects.filter(is_active=True, expiration_date__lt=today).values_list('product_id', flat=True)
        products = [p for p in products if p.id in list(ids)]

    rows = []
    for p in products:
        active_lots   = p.lots.filter(is_active=True)
        expired_lots  = active_lots.filter(expiration_date__lt=today).count()
        expiring_lots = active_lots.filter(
            expiration_date__range=[today, today + timedelta(days=7)]
        ).count()
        rows.append({
            'product':       p,
            'total_stock':   p.get_total_stock(),
            'is_low':        p.is_below_min_stock(),
            'expired_lots':  expired_lots,
            'expiring_lots': expiring_lots,
            'lot_count':     active_lots.count(),
        })

    return render(request, 'reports/inventory.html', {
        'rows':          rows,
        'filter_status': filter_status,
        'today':         today,
    })


@login_required
@_require_supervisor
def report_tasks(request):
    today     = timezone.now().date()
    date_from = request.GET.get('date_from', str(today - timedelta(days=30)))
    date_to   = request.GET.get('date_to',   str(today))
    client_id = request.GET.get('client', '')
    status_f  = request.GET.get('status', '')

    tasks = Task.objects.select_related('client', 'location', 'assigned_to').filter(
        scheduled_date__range=[date_from, date_to]
    )
    if client_id:
        tasks = tasks.filter(client_id=client_id)
    if status_f:
        tasks = tasks.filter(status=status_f)

    summary      = tasks.values('status').annotate(total=Count('id'))
    summary_dict = {s['status']: s['total'] for s in summary}
    clients      = Client.objects.filter(is_active=True)

    return render(request, 'reports/tasks.html', {
        'tasks':          tasks,
        'summary_dict':   summary_dict,
        'clients':        clients,
        'date_from':      date_from,
        'date_to':        date_to,
        'client_id':      client_id,
        'status_f':       status_f,
        'status_choices': Task.STATUS_CHOICES,
        'today':          today,
    })


@login_required
@_require_supervisor
def report_consumption(request):
    today     = timezone.now().date()
    date_from = request.GET.get('date_from', str(today - timedelta(days=30)))
    date_to   = request.GET.get('date_to',   str(today))
    client_id = request.GET.get('client', '')

    movements = Movement.objects.filter(
        movement_type=Movement.OUTSIDE,
        date__date__range=[date_from, date_to]
    ).select_related('lot__product', 'created_by')

    by_product = {}
    for m in movements:
        name = m.lot.product.name
        unit = m.lot.product.unit
        if name not in by_product:
            by_product[name] = {'unit': unit, 'total': 0, 'count': 0}
        by_product[name]['total'] += m.quantity
        by_product[name]['count'] += 1

    by_product_list = sorted(by_product.items(), key=lambda x: x[1]['total'], reverse=True)
    clients         = Client.objects.filter(is_active=True)

    return render(request, 'reports/consumption.html', {
        'movements':       movements,
        'by_product_list': by_product_list,
        'clients':         clients,
        'date_from':       date_from,
        'date_to':         date_to,
        'client_id':       client_id,
    })


@login_required
@_require_supervisor
def report_clients(request):
    today     = timezone.now().date()
    date_from = request.GET.get('date_from', str(today - timedelta(days=30)))
    date_to   = request.GET.get('date_to',   str(today))

    clients = Client.objects.filter(is_active=True).prefetch_related('tasks', 'locations')

    rows = []
    for c in clients:
        c_tasks = c.tasks.filter(scheduled_date__range=[date_from, date_to])
        rows.append({
            'client':    c,
            'total':     c_tasks.count(),
            'validated': c_tasks.filter(status=Task.VALIDATED).count(),
            'pending':   c_tasks.filter(status__in=[Task.PENDING, Task.IN_PROGRESS]).count(),
            'in_review': c_tasks.filter(status=Task.PENDING_REVIEW).count(),
        })

    rows.sort(key=lambda x: x['total'], reverse=True)

    return render(request, 'reports/clients.html', {
        'rows':      rows,
        'date_from': date_from,
        'date_to':   date_to,
    })


@login_required
@_require_supervisor
def report_low_stock(request):
    today = timezone.now().date()

    low_products  = [p for p in Product.objects.filter(is_active=True) if p.is_below_min_stock()]
    expiring_lots = Lot.objects.filter(
        is_active=True,
        expiration_date__range=[today, today + timedelta(days=7)]
    ).select_related('product').order_by('expiration_date')
    expired_lots  = Lot.objects.filter(
        is_active=True,
        expiration_date__lt=today
    ).select_related('product').order_by('expiration_date')

    return render(request, 'reports/low_stock.html', {
        'low_products':  low_products,
        'expiring_lots': expiring_lots,
        'expired_lots':  expired_lots,
        'today':         today,
    })
