from functools import wraps 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from .models import User
from .forms import UserCreateForm, UserEditForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')  
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('users:dashboard')  
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('users:login')


@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html', {'user': request.user})


def admin_required(view_func):
    @wraps(view_func)  
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def user_list(request):
    active_filter = request.GET.get('active', 'true')

    if active_filter == 'false':
        users = User.objects.filter(is_active=False).prefetch_related('groups').order_by('username')
    else:
        users = User.objects.filter(is_active=True).prefetch_related('groups').order_by('username')

    # Filtro por rol
    rol_filter = request.GET.get('rol', '')
    if rol_filter:
        users = users.filter(groups__id=rol_filter)

    grupos = Group.objects.all()

    return render(request, 'users/user_list.html', {
        'users': users,
        'active_filter': active_filter == 'true',
        'rol_filter': rol_filter,
        'grupos': grupos,
        'title': 'Usuarios Activos' if active_filter == 'true' else 'Usuarios Inactivos',
    })




@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            rol = form.cleaned_data['rol']
            user.groups.set([rol])
            messages.success(request, f'Usuario {user.username} creado correctamente.')
            return redirect('users:user_list')
    else:
        form = UserCreateForm()
    return render(request, 'users/user_form.html', {'form': form, 'action': 'Crear'})


@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            rol = form.cleaned_data['rol']
            user.groups.set([rol])
            messages.success(request, f'Usuario {user.username} actualizado.')
            return redirect('users:user_list')
    else:
        current_group = user.groups.first()
        form = UserEditForm(instance=user, initial={'rol': current_group})
    return render(request, 'users/user_form.html', {'form': form, 'action': 'Editar', 'obj': user})


@login_required
@admin_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'No podés desactivar tu propio usuario.')
        return redirect('users:user_list')
    user.is_active = not user.is_active
    user.save()
    estado = 'activado' if user.is_active else 'desactivado'
    messages.success(request, f'Usuario {user.username} {estado}.')
    return redirect('users:user_list')

