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
        # Solo operarios activos pueden ser asignados a tareas
        try:
            operario_group = Group.objects.get(name='Operario')
            self.fields['assigned_to'].queryset = User.objects.filter(
                groups=operario_group, is_active=True
            ).distinct().order_by('first_name', 'last_name')
        except Group.DoesNotExist:
            self.fields['assigned_to'].queryset = User.objects.none()

        self.fields['assigned_to'].empty_label = '— Seleccionar operario —'
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

    def clean(self):
        cleaned = super().clean()
        assigned_to    = cleaned.get('assigned_to')
        scheduled_date = cleaned.get('scheduled_date')
        scheduled_time = cleaned.get('scheduled_time')

        if assigned_to and scheduled_date and scheduled_time:
            qs = Task.objects.filter(
                assigned_to=assigned_to,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                status__in=[Task.PENDING, Task.IN_PROGRESS],
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f'{assigned_to.get_full_name() or assigned_to.username} ya tiene '
                    f'una tarea asignada el {scheduled_date} a las {scheduled_time}.'
                )
        return cleaned


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


class TaskMaterialUsedForm(forms.ModelForm):
    """
    Formulario para que el operario reporte la cantidad real usada de un material.
    La cantidad usada no puede superar la cantidad asignada.
    """
    class Meta:
        model  = TaskMaterial
        fields = ['quantity_used']
        widgets = {
            'quantity_used': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'quantity_used': 'Cantidad realmente usada',
        }

    def clean_quantity_used(self):
        qty_used = self.cleaned_data.get('quantity_used')
        if qty_used is None:
            raise forms.ValidationError('Ingresá la cantidad usada.')
        if qty_used < 0:
            raise forms.ValidationError('La cantidad no puede ser negativa.')
        if qty_used > self.instance.quantity:
            raise forms.ValidationError(
                f'No podés haber usado más de lo asignado ({self.instance.quantity} {self.instance.lot.product.unit}).'
            )
        return qty_used


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
