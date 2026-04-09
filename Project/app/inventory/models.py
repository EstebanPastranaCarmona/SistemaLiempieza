from django.db import models
from django.utils import timezone


class Product(models.Model):
    name               = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    product_type       = models.CharField(max_length=60, verbose_name='Tipo')
    unit               = models.CharField(max_length=30, verbose_name='Unidad de medida')
    min_stock          = models.IntegerField(default=0, verbose_name='Stock mínimo')
    supplier           = models.CharField(max_length=150, blank=True, verbose_name='Proveedor')
    warehouse_location = models.CharField(max_length=100, blank=True, verbose_name='Ubicación en almacén')
    is_active          = models.BooleanField(default=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    def get_total_stock(self):
        result = self.lots.filter(is_active=True).aggregate(total=models.Sum('quantity'))
        return result['total'] or 0

    def is_below_min_stock(self):
        return self.get_total_stock() < self.min_stock

    def archive(self):
        """Archiva el producto y todos sus lotes activos en cascada."""
        self.is_active = False
        self.save()
        self.lots.filter(is_active=True).update(is_active=False)

    def unarchive(self):
        """Desarchiva el producto. Los lotes NO se reactivan automáticamente
        para evitar reactivar lotes vencidos o inconsistentes."""
        self.is_active = True
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name        = 'Producto'
        verbose_name_plural = 'Productos'
        ordering            = ['name']


class Lot(models.Model):
    product         = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='lots', verbose_name='Producto')
    quantity        = models.IntegerField(verbose_name='Cantidad')
    expiration_date = models.DateField(verbose_name='Fecha de vencimiento')
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.expiration_date < timezone.now().date()

    def days_until_expiration(self):
        return (self.expiration_date - timezone.now().date()).days

    def __str__(self):
        return f'{self.product.name} — Lote #{self.id}'

    class Meta:
        verbose_name        = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering            = ['expiration_date']


class Movement(models.Model):
    INSIDE  = 'INSIDE'
    OUTSIDE = 'OUTSIDE'
    MOVEMENT_TYPES = [(INSIDE, 'Entrada'), (OUTSIDE, 'Salida')]

    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES, verbose_name='Tipo')
    lot           = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name='movements', verbose_name='Lote')
    quantity      = models.IntegerField(verbose_name='Cantidad')
    reason        = models.CharField(max_length=200, verbose_name='Motivo')
    date          = models.DateTimeField(auto_now_add=True)
    created_by    = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, related_name='movements', verbose_name='Registrado por'
    )

    def __str__(self):
        return f'{self.get_movement_type_display()} — {self.lot.product.name} ({self.quantity})'

    class Meta:
        verbose_name        = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        ordering            = ['-date']
