# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from uuid import uuid4


class User( AbstractUser ):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(unique=True, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        unique_together = ['username', 'email']

    def is_admin(self):
        return self.groups.filter(name='Administrador').exists()

    def is_supervisor(self):
        return self.groups.filter(name='Supervisor').exists()

    def is_operario(self):
        return self.groups.filter(name='Operario').exists()

    def get_rol(self):
        return self.groups.first().name if self.groups.exists() else 'Sin rol'

    def has_permission(self, code: str) -> bool:
        return self.user_permissions.filter(codename=code).exists() or \
               self.groups.filter(permissions__codename=code).exists()

