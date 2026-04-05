from django import forms
from .models import Task, TaskMaterial, Evidence, TaskReview
from app.clients.models import Client, ClientLocation
from app.users.models import User
from django.contrib.auth.models import Group


class TaskForm(forms.ModelForm):
    class Meta:
        model  = Task
        fields = ['title', 'description', 'client', 'location', 'assigned_to',
                  'scheduled_date', 'scheduled_time', 'notes']
        widgets = {
            'title':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la tarea'}),
            'description':    forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción (opcional)'}),
            'client':         forms.Select(attrs={'class': 'form-select', 'id': 'id_client'}),
            'location':       forms.Select(attrs={'class': 'form-select', 'id': 'id_location'}),
            'assigned_to':    forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes':          forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        operario_group = Group.objects.filter(name__in=['Operario', 'Supervisor'])
        self.fields['assigned_to'].queryset = User.objects.filter(
            groups__in=operario_group, is_active=True
        ).distinct()
        self.fields['assigned_to'].empty_label = '— Seleccionar trabajador —'
        self.fields['client'].empty_label = '— Seleccionar cliente —'
        self.fields['location'].queryset = ClientLocation.objects.none()
        self.fields['location'].required = False
        self.fields['location'].empty_label = '— Seleccionar ubicación (opcional) —'

        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['location'].queryset = ClientLocation.objects.filter(
                    client_id=client_id, is_active=True
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.client_id:
            self.fields['location'].queryset = ClientLocation.objects.filter(
                client=self.instance.client, is_active=True
            )


class TaskMaterialForm(forms.ModelForm):
    class Meta:
        model  = TaskMaterial
        fields = ['lot', 'quantity']
        widgets = {
            'lot':      forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.inventory.models import Lot
        self.fields['lot'].queryset = Lot.objects.filter(is_active=True).select_related('product')
        self.fields['lot'].empty_label = '— Seleccionar lote —'


class EvidenceForm(forms.ModelForm):
    class Meta:
        model  = Evidence
        fields = ['file', 'note']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Descripción de la evidencia...'
            }),
        }


class TaskReviewForm(forms.ModelForm):
    class Meta:
        model  = TaskReview
        fields = ['result', 'comment']
        widgets = {
            'result':  forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                             'placeholder': 'Comentario del supervisor (opcional)'}),
        }


class TaskCompleteForm(forms.ModelForm):
    """Formulario para que el operario envíe la tarea a revisión."""
    class Meta:
        model  = Task
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                           'placeholder': 'Observaciones finales (opcional)'}),
        }
