from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # CRUD usuarios — solo Administrador (CU5)
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/crear/', views.user_create, name='user_create'),
    path('usuarios/<uuid:pk>/editar/', views.user_edit, name='user_edit'),
    path('usuarios/<uuid:pk>/toggle/', views.user_toggle_active, name='user_toggle'),
]
