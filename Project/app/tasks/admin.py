from django.contrib import admin
from .models import Task, TaskMaterial, Evidence, TaskReview

admin.site.register(Task)
admin.site.register(TaskMaterial)
admin.site.register(Evidence)
admin.site.register(TaskReview)
