from django import forms
from .models import Product, Lot, Movement


class ProductForm(forms.ModelForm):
    class Meta:
        model  = Product
        fields = ['name', 'product_type', 'unit', 'min_stock', 'supplier', 'warehouse_location']
        labels = {
            'name':               'Nombre del producto',
            'product_type':       'Tipo / Categoría',
            'unit':               'Unidad de medida',
            'min_stock':          'Stock mínimo',
            'supplier':           'Proveedor',
            'warehouse_location': 'Ubicación en almacén',
        }
        widgets = {
            'name':               forms.TextInput(attrs={'class': 'form-control'}),
            'product_type':       forms.TextInput(attrs={'class': 'form-control'}),
            'unit':               forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: unidades, cajas, bolsas'}),
            'min_stock':          forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'supplier':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Distribuidora XYZ (opcional)'}),
            'warehouse_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Estante A-3 (opcional)'}),
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
        fields = ['product', 'quantity', 'expiration_date']
        labels = {
            'product':         'Producto',
            'quantity':        'Cantidad',
            'expiration_date': 'Fecha de vencimiento',
        }
        widgets = {
            'product':         forms.Select(attrs={'class': 'form-select'}),
            'quantity':        forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar productos activos (no archivados)
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar lotes activos (cuyo producto tampoco esté archivado)
        self.fields['lot'].queryset = Lot.objects.filter(
            is_active=True,
            product__is_active=True
        ).select_related('product').order_by('product__name', 'expiration_date')
