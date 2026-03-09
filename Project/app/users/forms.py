from django import forms
from django.contrib.auth.models import Group
import re
from .models import User

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Contraseña'
    )
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label='-- Seleccioná un rol --',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Rol'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ese nombre de usuario ya existe.')
        return username
    
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name'].strip()
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', first_name):
            raise forms.ValidationError('El nombre solo puede contener letras.')
        if len(first_name) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        return first_name.title()  # 👈 capitaliza automático: "juan" → "Juan"

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name'].strip()
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', last_name):
            raise forms.ValidationError('El apellido solo puede contener letras.')
        if len(last_name) < 2:
            raise forms.ValidationError('El apellido debe tener al menos 2 caracteres.')
        return last_name.title()


class UserEditForm(forms.ModelForm):
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label='-- Seleccioná un rol --',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Rol'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'rol']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ese correo ya está registrado.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ese nombre de usuario ya existe.')
        return username
    
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name'].strip()
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', first_name):
            raise forms.ValidationError('El nombre solo puede contener letras.')
        if len(first_name) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        return first_name.title()  

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name'].strip()
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', last_name):
            raise forms.ValidationError('El apellido solo puede contener letras.')
        if len(last_name) < 2:
            raise forms.ValidationError('El apellido debe tener al menos 2 caracteres.')
        return last_name.title()

