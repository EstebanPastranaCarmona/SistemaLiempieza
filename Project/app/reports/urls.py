from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('',           views.reports_dashboard,  name='dashboard'),
    path('inventario/', views.report_inventory,  name='inventory'),
    path('tareas/',     views.report_tasks,       name='tasks'),
    path('alertas/',    views.report_alerts,      name='alerts'),
    path('consumo/',    views.report_consumption, name='consumption'),
    path('clientes/',   views.report_clients,     name='clients'),
]
