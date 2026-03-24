from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('productos/', views.product_list, name='product_list'),
    path('productos/crear/', views.product_create, name='product_create'),
    path('productos/<int:pk>/editar/', views.product_edit, name='product_edit'),
    path('productos/<int:pk>/toggle/', views.product_toggle_active, name='product_toggle'),
    path('lotes/', views.lot_list, name='lot_list'),
    path('lotes/crear/', views.lot_create, name='lot_create'),
    path('movimientos/', views.movement_list, name='movement_list'),
    path('movimientos/crear/', views.movement_create, name='movement_create'),
    path('alertas/', views.alerts_dashboard, name='alerts'),
]
