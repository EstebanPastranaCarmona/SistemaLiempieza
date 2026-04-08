from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('',            views.report_index,     name='index'),
    path('inventario/', views.report_inventory, name='inventory'),
    path('tareas/',     views.report_tasks,     name='tasks'),
]
