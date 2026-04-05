from django import forms
from .models import Client, ClientLocation


class ClientForm(forms.ModelForm):
    class Meta:
        model  = Client
        fields = ['name', 'contact_name', 'phone', 'email']
        labels = {
            'name':         'Nombre de la empresa',
            'contact_name': 'Persona de contacto',
            'phone':        'Teléfono (opcional)',
            'email':        'Correo electrónico',
        }
        widgets = {
            'name':         forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'phone':        forms.TextInput(attrs={
                                'class': 'form-control',
                                'placeholder': 'ej: 88001122 (opcional)',
                                'maxlength': '20',
                            }),
            'email':        forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
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

    def clean_contact_name(self):
        val = self.cleaned_data.get('contact_name', '').strip()
        if not val:
            raise forms.ValidationError('La persona de contacto es obligatoria.')
        return val

    def clean_email(self):
        val = self.cleaned_data.get('email', '').strip()
        if not val:
            raise forms.ValidationError('El correo electrónico es obligatorio.')
        return val

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
    """Formulario de ubicación — el campo client se asigna en la vista, no se muestra al usuario."""
    class Meta:
        model  = ClientLocation
        fields = ['name', 'address', 'notes']
        labels = {
            'name':    'Nombre de la ubicación',
            'address': 'Dirección',
            'notes':   'Notas adicionales (opcional)',
        }
        widgets = {
            'name':    forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'notes':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
