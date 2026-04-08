from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('',                                    views.task_list,             name='task_list'),
    path('nueva/',                              views.task_create,           name='task_create'),
    path('<int:pk>/',                           views.task_detail,           name='task_detail'),
    path('<int:pk>/editar/',                    views.task_edit,             name='task_edit'),
    path('<int:pk>/iniciar/',                   views.task_start,            name='task_start'),
    path('<int:pk>/completar/',                 views.task_complete,         name='task_complete'),
    path('<int:task_pk>/evidencia/',            views.evidence_create,       name='evidence_create'),
    path('<int:task_pk>/material/',             views.task_material_create,  name='task_material_create'),
    path('material/<int:pk>/eliminar/',         views.task_material_delete,  name='task_material_delete'),
    path('<int:task_pk>/revision/',             views.task_review,           name='task_review'),
]
