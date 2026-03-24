from django.db import models


class Client(models.Model):
    name         = models.CharField(max_length=100, verbose_name='Nombre')
    contact_name = models.CharField(max_length=100, blank=True, verbose_name='Contacto')
    phone        = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    email        = models.EmailField(blank=True, verbose_name='Correo')
    address      = models.CharField(max_length=200, verbose_name='Dirección principal')
    is_active    = models.BooleanField(default=True, verbose_name='Activo')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name        = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering            = ['name']


class ClientLocation(models.Model):
    """Ubicación específica de un cliente donde se ejecutan las tareas de limpieza."""
    client   = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='locations', verbose_name='Cliente')
    name     = models.CharField(max_length=100, verbose_name='Nombre de la ubicación')
    address  = models.CharField(max_length=200, verbose_name='Dirección')
    notes    = models.TextField(blank=True, verbose_name='Notas')
    is_active = models.BooleanField(default=True, verbose_name='Activa')

    def __str__(self):
        return f'{self.client.name} — {self.name}'

    class Meta:
        verbose_name        = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering            = ['client', 'name']
        unique_together     = ('client', 'name')
