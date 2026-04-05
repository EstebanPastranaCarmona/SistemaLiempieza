from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Lista y detalle
    path('',                                  views.task_list,             name='task_list'),
    path('<int:pk>/',                         views.task_detail,           name='task_detail'),

    # CRUD de tareas
    path('nueva/',                            views.task_create,           name='task_create'),
    path('<int:pk>/editar/',                  views.task_edit,             name='task_edit'),
    path('<int:pk>/completar/',               views.task_complete,         name='task_complete'),

    # Evidencias
    path('<int:task_pk>/evidencia/nueva/',    views.evidence_create,       name='evidence_create'),

    # Materiales
    path('<int:task_pk>/material/nuevo/',     views.task_material_create,  name='task_material_create'),
    path('material/<int:pk>/eliminar/',       views.task_material_delete,  name='task_material_delete'),

    # Revisión supervisor
    path('<int:task_pk>/revision/',           views.task_review,           name='task_review'),
]
