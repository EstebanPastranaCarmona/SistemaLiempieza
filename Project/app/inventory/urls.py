from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Raíz → redirige a lotes
    path('', views.inventory_home, name='home'),

    # Lotes (principal)
    path('lotes/', views.lot_list, name='lot_list'),
    path('lotes/nuevo/', views.lot_create, name='lot_create'),
    path('lotes/<int:pk>/editar/', views.lot_edit, name='lot_edit'),
    path('lotes/<int:pk>/toggle/', views.lot_toggle_active, name='lot_toggle'),

    # Productos (secundario)
    path('productos/', views.product_list, name='product_list'),
    path('productos/nuevo/', views.product_create, name='product_create'),
    path('productos/<int:pk>/editar/', views.product_edit, name='product_edit'),
    path('productos/<int:pk>/toggle/', views.product_toggle_active, name='product_toggle'),

    # Movimientos
    path('movimientos/', views.movement_list, name='movement_list'),
    path('movimientos/nuevo/', views.movement_create, name='movement_create'),

    # Alertas
    path('alertas/', views.alerts_dashboard, name='alerts'),
]
