from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.users.urls')),
    path('clientes/', include('app.clients.urls')),
    path('inventario/', include('app.inventory.urls')),
    path('tareas/', include('app.tasks.urls')),
]

# Servir archivos media en desarrollo (evidencias, fotos, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
