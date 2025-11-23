from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import ComplaintCategory, ComplaintOption
from .models import WardenProfile
admin.site.register(WardenProfile)
admin.site.register(ComplaintCategory)
admin.site.register(ComplaintOption)