from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import ComplaintCategory, ComplaintOption

admin.site.register(ComplaintCategory)
admin.site.register(ComplaintOption)