from django import forms
from .models import Client, ClientLocation


class ClientForm(forms.ModelForm):
    class Meta:
        model  = Client
        fields = ['name', 'contact_name', 'phone', 'email', 'address']
        labels = {
            'name':         'Nombre de la empresa',
            'contact_name': 'Persona de contacto',
            'phone':        'Teléfono',
            'email':        'Correo electrónico',
            'address':      'Dirección principal',
        }
        widgets = {
            'name':         forms.TextInput(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone':        forms.TextInput(attrs={
                                'class': 'form-control',
                                'placeholder': 'ej: 88001122',
                                'pattern': r'[0-9\+\-\s\(\)]{7,20}',
                                'title': 'Solo números, espacios, guiones o paréntesis (7-20 caracteres)',
                                'maxlength': '20',
                            }),
            'email':        forms.EmailInput(attrs={'class': 'form-control'}),
            'address':      forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        qs = Client.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un cliente con ese nombre.')
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            return phone
        import re
        digits = re.sub(r'[^0-9]', '', phone)
        if len(digits) < 7 or len(digits) > 15:
            raise forms.ValidationError('El teléfono debe tener entre 7 y 15 dígitos.')
        if not re.match(r'^[0-9\+\-\s\(\)]+$', phone):
            raise forms.ValidationError('Solo se permiten números, espacios, guiones y paréntesis.')
        return phone


class ClientLocationForm(forms.ModelForm):
    class Meta:
        model  = ClientLocation
        fields = ['client', 'name', 'address', 'notes']
        labels = {
            'client':  'Cliente',
            'name':    'Nombre de la ubicación',
            'address': 'Dirección',
            'notes':   'Notas adicionales',
        }
        widgets = {
            'client':  forms.Select(attrs={'class': 'form-select'}),
            'name':    forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'notes':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
