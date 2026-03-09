from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_rol', 'is_active')
    list_filter = ('groups', 'is_active')
    search_fields = ('username', 'email')

    def get_rol(self, obj):
        return obj.get_rol()
    get_rol.short_description = 'Rol'

