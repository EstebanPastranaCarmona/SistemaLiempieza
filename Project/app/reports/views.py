import csv
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify
from functools import wraps


def _require_supervisor(view_func):
    """Solo supervisores y admins pueden ver reportes."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('users:login')
        if not (request.user.is_admin or request.user.is_supervisor):
            messages.error(request, 'Los reportes son solo para supervisores y administradores.')
            from django.shortcuts import redirect
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@_require_supervisor
def index(request):
    """Dashboard principal de reportes con KPIs."""
    from app.inventory.models import Product, Lot, Movement
    from app.tasks.models import Task
    from app.clients.models import Client

    today = timezone.now().date()

    # KPIs de inventario
    products      = Product.objects.filter(is_active=True)
    low_stock     = [p for p in products if p.is_below_min_stock()]
    expiring_lots = Lot.objects.filter(is_active=True, expiration_date__lte=today + timezone.timedelta(days=30)).count()
    expired_lots  = Lot.objects.filter(is_active=True, expiration_date__lt=today).count()

    # KPIs de tareas
    total_tasks     = Task.objects.count()
    validated_tasks = Task.objects.filter(status=Task.VALIDATED).count()
    pending_review  = Task.objects.filter(status=Task.PENDING_REVIEW).count()
    overdue_tasks   = [
        t for t in Task.objects.filter(status__in=[Task.PENDING, Task.IN_PROGRESS])
        if t.is_overdue()
    ]

    context = {
        'low_stock_count':     len(low_stock),
        'expiring_lots_count': expiring_lots,
        'expired_lots_count':  expired_lots,
        'total_tasks':         total_tasks,
        'validated_tasks':     validated_tasks,
        'pending_review':      pending_review,
        'overdue_count':       len(overdue_tasks),
        'client_count':        Client.objects.filter(is_active=True).count(),
    }
    return render(request, 'reports/index.html', context)


@login_required
@_require_supervisor
def inventario(request):
    from app.inventory.models import Product
    products = Product.objects.filter(is_active=True).prefetch_related('lots')

    # CU8: exportar CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="inventario.csv"'
        response.write('\ufeff')  # BOM para Excel
        writer = csv.writer(response)
        writer.writerow(['Producto', 'Tipo', 'Unidad', 'Stock total', 'Mínimo', 'Proveedor', 'Ubicación almacén', 'Estado stock'])
        for p in products:
            writer.writerow([
                p.name, p.product_type, p.unit,
                p.get_total_stock(), p.min_stock,
                p.supplier or '—', p.warehouse_location or '—',
                'BAJO' if p.is_below_min_stock() else 'OK',
            ])
        return response

    search = request.GET.get('q', '')
    if search:
        products = products.filter(name__icontains=search)
    return render(request, 'reports/inventario.html', {'products': products, 'search': search})


@login_required
@_require_supervisor
def tareas(request):
    from app.tasks.models import Task
    tasks = Task.objects.all().select_related('client', 'location', 'assigned_to', 'created_by')

    # Filtros
    status_filter = request.GET.get('status', '')
    client_filter = request.GET.get('client', '')
    date_from     = request.GET.get('date_from', '')
    date_to       = request.GET.get('date_to', '')

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if client_filter:
        tasks = tasks.filter(client_id=client_filter)
    if date_from:
        tasks = tasks.filter(scheduled_date__gte=date_from)
    if date_to:
        tasks = tasks.filter(scheduled_date__lte=date_to)

    tasks = tasks.order_by('-scheduled_date')

    # CU8: exportar CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="tareas.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Título', 'Cliente', 'Ubicación', 'Asignado a', 'Fecha programada', 'Hora', 'Estado', 'Creado por'])
        status_labels = dict(Task.STATUS_CHOICES)
        for t in tasks:
            writer.writerow([
                t.title,
                t.client.name,
                t.location.name if t.location else '—',
                t.assigned_to.get_full_name() or t.assigned_to.username if t.assigned_to else '—',
                t.scheduled_date,
                t.scheduled_time or '—',
                status_labels.get(t.status, t.status),
                t.created_by.get_full_name() or t.created_by.username if t.created_by else '—',
            ])
        return response

    from app.clients.models import Client
    context = {
        'tasks':          tasks,
        'status_choices': Task.STATUS_CHOICES,
        'clients':        Client.objects.filter(is_active=True),
        'status_filter':  status_filter,
        'client_filter':  client_filter,
        'date_from':      date_from,
        'date_to':        date_to,
    }
    return render(request, 'reports/tareas.html', context)


@login_required
@_require_supervisor
def consumo(request):
    from app.inventory.models import Movement
    from django.db.models import Sum

    movements = Movement.objects.filter(
        movement_type=Movement.OUTSIDE
    ).select_related('lot__product', 'created_by').order_by('-date')

    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    if date_from:
        movements = movements.filter(date__date__gte=date_from)
    if date_to:
        movements = movements.filter(date__date__lte=date_to)

    # CU8: exportar CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="consumo.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Producto', 'Lote #', 'Cantidad', 'Unidad', 'Motivo', 'Registrado por'])
        for m in movements:
            writer.writerow([
                m.date.strftime('%d/%m/%Y %H:%M'),
                m.lot.product.name,
                m.lot.pk,
                m.quantity,
                m.lot.product.unit,
                m.reason,
                m.created_by.get_full_name() or m.created_by.username if m.created_by else '—',
            ])
        return response

    context = {
        'movements': movements,
        'date_from': date_from,
        'date_to':   date_to,
    }
    return render(request, 'reports/consumo.html', context)


@login_required
@_require_supervisor
def clientes(request):
    from app.clients.models import Client
    from app.tasks.models import Task

    clients_data = []
    for client in Client.objects.filter(is_active=True):
        total     = Task.objects.filter(client=client).count()
        validated = Task.objects.filter(client=client, status=Task.VALIDATED).count()
        pct = round((validated / total * 100) if total > 0 else 0, 1)
        clients_data.append({
            'client':    client,
            'total':     total,
            'validated': validated,
            'pct':       pct,
        })

    # CU8: exportar CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="clientes.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Cliente', 'Total tareas', 'Validadas', '% cumplimiento'])
        for row in clients_data:
            writer.writerow([row['client'].name, row['total'], row['validated'], f"{row['pct']}%"])
        return response

    return render(request, 'reports/clientes.html', {'clients_data': clients_data})


@login_required
@_require_supervisor
def stock_bajo(request):
    from app.inventory.models import Product, Lot
    from django.utils import timezone

    today = timezone.now().date()

    products  = Product.objects.filter(is_active=True)
    low_stock = [p for p in products if p.is_below_min_stock()]

    expiring_lots = Lot.objects.filter(
        is_active=True,
        expiration_date__lte=today + timezone.timedelta(days=30)
    ).select_related('product').order_by('expiration_date')

    # CU8: exportar CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="alertas_stock.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Tipo alerta', 'Producto', 'Detalle'])
        for p in low_stock:
            writer.writerow(['Stock bajo', p.name, f"Stock actual: {p.get_total_stock()} / Mínimo: {p.min_stock} {p.unit}"])
        for lot in expiring_lots:
            estado = 'VENCIDO' if lot.expiration_date < today else f'Vence en {lot.days_until_expiration()} días'
            writer.writerow(['Lote por vencer', f"{lot.product.name} #{lot.pk}", f"{lot.expiration_date} — {estado}"])
        return response

    context = {
        'low_stock':     low_stock,
        'expiring_lots': expiring_lots,
        'today':         today,
    }
    return render(request, 'reports/stock_bajo.html', context)
