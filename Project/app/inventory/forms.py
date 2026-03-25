from django import forms
from .models import Product, Lot, Movement


class ProductForm(forms.ModelForm):
    class Meta:
        model  = Product
        fields = ['name', 'product_type', 'unit', 'min_stock']
        labels = {
            'name':         'Nombre del producto',
            'product_type': 'Tipo / Categoría',
            'unit':         'Unidad de medida',
            'min_stock':    'Stock mínimo',
        }
        widgets = {
            'name':         forms.TextInput(attrs={'class': 'form-control'}),
            'product_type': forms.TextInput(attrs={'class': 'form-control'}),
            'unit':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: unidades, cajas, bolsas'}),
            'min_stock':    forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        qs = Product.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un producto con ese nombre.')
        return name


class LotForm(forms.ModelForm):
    class Meta:
        model  = Lot
        fields = ['product', 'quantity', 'expiration_date', 'cost']
        labels = {
            'product':         'Producto',
            'quantity':        'Cantidad',
            'expiration_date': 'Fecha de vencimiento',
            'cost':            'Costo unitario',
        }
        widgets = {
            'product':         forms.Select(attrs={'class': 'form-select'}),
            'quantity':        forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cost':            forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }


class MovementForm(forms.ModelForm):
    class Meta:
        model  = Movement
        fields = ['movement_type', 'lot', 'quantity', 'reason']
        labels = {
            'movement_type': 'Tipo de movimiento',
            'lot':           'Lote',
            'quantity':      'Cantidad',
            'reason':        'Motivo',
        }
        widgets = {
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'lot':           forms.Select(attrs={'class': 'form-select'}),
            'quantity':      forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
            'reason':        forms.TextInput(attrs={'class': 'form-control'}),
        }
