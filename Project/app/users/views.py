from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import User
from .forms import UserCreateForm, UserEditForm
from functools import wraps


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not request.user.is_admin:
            messages.error(request, 'Esta sección es solo para administradores.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('users:dashboard')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('users:login')


@login_required
def dashboard(request):
    from app.inventory.models import Product
    from app.tasks.models import Task
    from django.utils import timezone

    context = {}

    # CU4: alertas activas en dashboard para admin/supervisor
    if request.user.is_admin or request.user.is_supervisor:
        today    = timezone.now().date()
        products = Product.objects.filter(is_active=True)

        low_stock_products = [p for p in products if p.is_below_min_stock()]

        from app.inventory.models import Lot
        expiring_lots = Lot.objects.filter(
            is_active=True,
            expiration_date__lte=today + timezone.timedelta(days=30)
        ).select_related('product').order_by('expiration_date')

        expired_lots = Lot.objects.filter(
            is_active=True,
            expiration_date__lt=today
        ).select_related('product')

        context['low_stock_count']   = len(low_stock_products)
        context['expiring_count']    = expiring_lots.count()
        context['expired_count']     = expired_lots.count()
        context['low_stock_list']    = low_stock_products[:5]
        context['expiring_list']     = expiring_lots[:5]
        context['has_stock_alerts']  = len(low_stock_products) > 0 or expired_lots.exists()

        # Tareas pendientes de revisión
        pending_review = Task.objects.filter(status=Task.PENDING_REVIEW).count()
        context['pending_review_count'] = pending_review

    # CU7: para operarios — notificar si alguna tarea propia fue rechazada
    if request.user.is_operario:
        from app.tasks.models import TaskReview
        rejected_tasks = Task.objects.filter(
            assigned_to=request.user,
            status=Task.IN_PROGRESS,
            review__result=TaskReview.REJECTED
        ).select_related('review')
        context['rejected_tasks'] = rejected_tasks

        # Tareas propias del operario
        my_tasks = Task.objects.filter(
            assigned_to=request.user
        ).exclude(status=Task.VALIDATED).order_by('scheduled_date', 'scheduled_time')
        context['my_tasks'] = my_tasks

    return render(request, 'users/dashboard.html', context)


@login_required
@admin_required
def user_list(request):
    # Leer filtros desde GET
    active_param = request.GET.get('active', 'true')   # 'true' | 'false' | '' (todos)
    rol_filter   = request.GET.get('rol', '')           # id del grupo o ''

    # Filtro activo/inactivo
    if active_param == 'true':
        active_filter = True
        users = User.objects.filter(is_active=True)
    elif active_param == 'false':
        active_filter = False
        users = User.objects.filter(is_active=False)
    else:
        active_filter = None
        users = User.objects.all()

    # Filtro por rol (grupo)
    if rol_filter:
        users = users.filter(groups__id=rol_filter)

    users = users.prefetch_related('groups').order_by('username')
    grupos = Group.objects.all()

    return render(request, 'users/user_list.html', {
        'users':        users,
        'grupos':       grupos,
        'active_filter': active_filter,
        'rol_filter':   rol_filter,
        'active_param': active_param,
    })


@login_required
@admin_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        # 'rol' devuelve directamente el objeto Group (ModelChoiceField)
        group = form.cleaned_data.get('rol')
        if group:
            user.groups.add(group)
        messages.success(request, f'Usuario {user.username} creado correctamente.')
        return redirect('users:user_list')
    return render(request, 'users/user_form.html', {'form': form, 'action': 'Crear'})


@login_required
@admin_required
def user_edit(request, pk):
    user_obj = User.objects.get(pk=pk)
    # Precarga el grupo actual en el campo 'rol'
    current_group = user_obj.groups.first()
    initial = {'rol': current_group} if current_group else {}
    form = UserEditForm(request.POST or None, instance=user_obj, initial=initial)
    if form.is_valid():
        user_obj = form.save()
        # 'rol' devuelve directamente el objeto Group (ModelChoiceField)
        group = form.cleaned_data.get('rol')
        if group:
            user_obj.groups.set([group])  # reemplaza cualquier grupo anterior
        messages.success(request, 'Usuario actualizado.')
        return redirect('users:user_list')
    return render(request, 'users/user_form.html', {'form': form, 'action': 'Editar', 'obj': user_obj})


@login_required
@admin_required
def user_toggle_active(request, pk):
    from django.views.decorators.http import require_POST
    user_obj          = User.objects.get(pk=pk)
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    estado = 'activado' if user_obj.is_active else 'desactivado'
    messages.success(request, f'Usuario {user_obj.username} {estado}.')
    return redirect('users:user_list')
