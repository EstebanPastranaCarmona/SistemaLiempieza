from django.contrib import admin
from .models import Product, Lot, Movement

admin.site.register(Product)
admin.site.register(Lot)
admin.site.register(Movement)
