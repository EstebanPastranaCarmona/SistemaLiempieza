from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Product, Lot, Movement
from .forms import ProductForm, LotForm, MovementForm
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


# ── Raíz: siempre redirige a lotes ──────────────────────────────
@login_required
def inventory_home(request):
    return redirect('inventory:lot_list')


# ── Lotes ────────────────────────────────────────────────

@login_required
@supervisor_or_admin_required
def lot_list(request):
    lots  = Lot.objects.filter(is_active=True).select_related('product').order_by('expiration_date')
    today = timezone.now().date()
    return render(request, 'inventory/lot_list.html', {'lots': lots, 'today': today})


@login_required
@admin_required
def lot_create(request):
    form = LotForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Lote registrado correctamente.')
        return redirect('inventory:lot_list')
    return render(request, 'inventory/lot_form.html', {'form': form, 'action': 'Nuevo'})


@login_required
@admin_required
def lot_edit(request, pk):
    lot  = get_object_or_404(Lot, pk=pk)
    form = LotForm(request.POST or None, instance=lot)
    if form.is_valid():
        form.save()
        messages.success(request, 'Lote actualizado.')
        return redirect('inventory:lot_list')
    return render(request, 'inventory/lot_form.html', {'form': form, 'action': 'Editar', 'lot': lot})


@login_required
@admin_required
@require_POST
def lot_toggle_active(request, pk):
    lot           = get_object_or_404(Lot, pk=pk)
    lot.is_active = not lot.is_active
    lot.save()
    estado = 'activado' if lot.is_active else 'archivado'
    messages.success(request, f'Lote #{lot.pk} ({lot.product.name}) {estado}.')
    return redirect('inventory:lot_list')


# ── Productos (secundario) ───────────────────────────────

@login_required
@supervisor_or_admin_required
def product_list(request):
    show = request.GET.get('show', 'active')
    if show == 'archived':
        products      = Product.objects.filter(is_active=False)
        low_stock_ids = []
    elif show == 'all':
        products      = Product.objects.all()
        low_stock_ids = [p.id for p in products if p.is_active and p.is_below_min_stock()]
    else:  # 'active' (default)
        products      = Product.objects.filter(is_active=True)
        low_stock_ids = [p.id for p in products if p.is_below_min_stock()]
    return render(request, 'inventory/product_list.html', {
        'products':      products,
        'low_stock_ids': low_stock_ids,
        'show':          show,
    })


@login_required
@admin_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto creado correctamente.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'action': 'Crear'})


@login_required
@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form    = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'action': 'Editar', 'obj': product})


@login_required
@admin_required
@require_POST
def product_toggle_active(request, pk):
    """Toggle archivar/desarchivar. Al archivar, archiva lotes en cascada.
    Al desarchivar, solo reactiva el producto; los lotes se gestionan manualmente."""
    product = get_object_or_404(Product, pk=pk)
    if product.is_active:
        lots_count = product.lots.filter(is_active=True).count()
        product.archive()
        messages.success(
            request,
            f'Producto "{product.name}" archivado junto con {lots_count} lote(s) activo(s).'
        )
        return redirect('inventory:product_list')
    else:
        product.unarchive()
        messages.success(
            request,
            f'Producto "{product.name}" desarchivado. Podés reactivar sus lotes manualmente desde la sección de Lotes.'
        )
        return redirect(f"{{% url 'inventory:product_list' %}}?show=archived")


# ── Movimientos ─────────────────────────────────────────────

@login_required
@supervisor_or_admin_required
def movement_list(request):
    movements = Movement.objects.all().select_related('lot__product', 'created_by').order_by('-date')
    return render(request, 'inventory/movement_list.html', {'movements': movements})


@login_required
@supervisor_or_admin_required
def movement_create(request):
    form = MovementForm(request.POST or None)
    if form.is_valid():
        movement            = form.save(commit=False)
        movement.created_by = request.user
        if movement.movement_type == Movement.OUTSIDE:
            if movement.lot.quantity < movement.quantity:
                messages.error(request, 'Stock insuficiente en el lote seleccionado.')
                return render(request, 'inventory/movement_form.html', {'form': form, 'action': 'Registrar'})
            movement.lot.quantity -= movement.quantity
            movement.lot.save()
        else:
            movement.lot.quantity += movement.quantity
            movement.lot.save()
        movement.save()
        messages.success(request, 'Movimiento registrado.')
        return redirect('inventory:movement_list')
    return render(request, 'inventory/movement_form.html', {'form': form, 'action': 'Registrar'})


# ── Alertas ───────────────────────────────────────────────

@login_required
@supervisor_or_admin_required
def alerts_dashboard(request):
    today        = timezone.now().date()
    products     = Product.objects.filter(is_active=True)
    low_stock    = [p for p in products if p.is_below_min_stock()]
    expiring_lots = Lot.objects.filter(
        is_active=True,
        expiration_date__lte=today + timezone.timedelta(days=30)
    ).select_related('product').order_by('expiration_date')
    return render(request, 'inventory/alerts.html', {
        'low_stock':     low_stock,
        'expiring_lots': expiring_lots,
        'today':         today,
    })
