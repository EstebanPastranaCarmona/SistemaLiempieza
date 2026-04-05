from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.users.urls')),
    path('clientes/', include('app.clients.urls')),
    path('inventario/', include('app.inventory.urls')),
    path('tareas/', include('app.tasks.urls')),
]
