from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('crear/', views.client_create, name='client_create'),
    path('<int:pk>/editar/', views.client_edit, name='client_edit'),
    path('<int:pk>/toggle/', views.client_toggle_active, name='client_toggle'),
    path('<int:client_pk>/ubicaciones/', views.location_list, name='location_list'),
    path('<int:client_pk>/ubicaciones/json/', views.locations_json, name='locations_json'),
    path('<int:client_pk>/ubicaciones/crear/', views.location_create, name='location_create'),
    path('ubicaciones/<int:pk>/editar/', views.location_edit, name='location_edit'),
]
