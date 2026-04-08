from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Client, ClientLocation
from .forms import ClientForm, ClientLocationForm
from app.users.views import admin_required


@login_required
@admin_required
def client_list(request):
    active_filter = request.GET.get('active', 'true')
    if active_filter == 'false':
        clients = Client.objects.filter(is_active=False).prefetch_related('locations')
    else:
        clients = Client.objects.filter(is_active=True).prefetch_related('locations')
    return render(request, 'clients/client_list.html', {
        'clients': clients,
        'active_filter': active_filter == 'true',
        'title': 'Clientes Activos' if active_filter == 'true' else 'Clientes Inactivos',
    })


@login_required
@admin_required
def client_create(request):
    form = ClientForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cliente creado correctamente.')
        return redirect('clients:client_list')
    return render(request, 'clients/client_form.html', {'form': form, 'action': 'Crear'})


@login_required
@admin_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cliente actualizado.')
        return redirect('clients:client_list')
    return render(request, 'clients/client_form.html', {'form': form, 'action': 'Editar', 'obj': client})


@login_required
@admin_required
@require_POST
def client_toggle_active(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client.is_active = not client.is_active
    client.save()
    estado = 'activado' if client.is_active else 'desactivado'
    messages.success(request, f'Cliente {client.name} {estado}.')
    return redirect('clients:client_list')


@login_required
@admin_required
def location_list(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    locations = client.locations.all()
    return render(request, 'clients/location_list.html', {'client': client, 'locations': locations})


@login_required
def locations_json(request, client_pk):
    """Endpoint AJAX: devuelve las ubicaciones activas de un cliente en JSON."""
    locations = ClientLocation.objects.filter(client_id=client_pk, is_active=True).values('id', 'name')
    return JsonResponse(list(locations), safe=False)


@login_required
@admin_required
def location_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    form = ClientLocationForm(request.POST or None)
    if form.is_valid():
        location = form.save(commit=False)
        location.client = client          # asignamos el cliente desde la URL
        location.save()
        messages.success(request, 'Ubicación agregada.')
        return redirect('clients:location_list', client_pk=client.pk)
    return render(request, 'clients/location_form.html', {'form': form, 'action': 'Agregar', 'client': client})


@login_required
@admin_required
def location_edit(request, pk):
    location = get_object_or_404(ClientLocation, pk=pk)
    form = ClientLocationForm(request.POST or None, instance=location)
    if form.is_valid():
        loc = form.save(commit=False)
        loc.client = location.client      # protegemos que no cambie de cliente
        loc.save()
        messages.success(request, 'Ubicación actualizada.')
        return redirect('clients:location_list', client_pk=location.client.pk)
    return render(request, 'clients/location_form.html', {'form': form, 'action': 'Editar', 'client': location.client})
