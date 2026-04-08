from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('',            views.index,      name='index'),
    path('inventario/', views.inventario, name='inventario'),
    path('tareas/',     views.tareas,     name='tareas'),
    path('consumo/',    views.consumo,    name='consumo'),
    path('clientes/',   views.clientes,   name='clientes'),
    path('stock-bajo/', views.stock_bajo, name='stock_bajo'),
]
