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
        if not (request.user.is_admin() or request.user.is_supervisor()):
            messages.error(request, 'No tenés permisos para acceder a esta sección.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Productos ────────────────────────────────────────────

@login_required
@supervisor_or_admin_required
def product_list(request):
    products = Product.objects.filter(is_active=True)
    low_stock = [p for p in products if p.is_below_min_stock()]
    return render(request, 'inventory/product_list.html', {
        'products': products,
        'low_stock_ids': [p.id for p in low_stock],
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
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'action': 'Editar', 'obj': product})


@login_required
@admin_required
@require_POST
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    estado = 'activado' if product.is_active else 'desactivado'
    messages.success(request, f'Producto {product.name} {estado}.')
    return redirect('inventory:product_list')


# ── Lotes ──────────────────────────────────────────────

@login_required
@supervisor_or_admin_required
def lot_list(request):
    lots = Lot.objects.filter(is_active=True).select_related('product').order_by('expiration_date')
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


# ── Movimientos ──────────────────────────────────────────

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
        movement = form.save(commit=False)
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


# ── Alertas ─────────────────────────────────────────────

@login_required
@supervisor_or_admin_required
def alerts_dashboard(request):
    today = timezone.now().date()
    products = Product.objects.filter(is_active=True)
    low_stock = [p for p in products if p.is_below_min_stock()]
    expiring_lots = Lot.objects.filter(
        is_active=True,
        expiration_date__lte=today + timezone.timedelta(days=30)
    ).select_related('product').order_by('expiration_date')
    return render(request, 'inventory/alerts.html', {
        'low_stock': low_stock,
        'expiring_lots': expiring_lots,
        'today': today,
    })
