from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class WardenProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    photo_url = models.URLField(blank=True)

    def __str__(self):
        return self.user.get_full_name()


class ComplaintCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ComplaintOption(models.Model):
    category = models.ForeignKey(ComplaintCategory, on_delete=models.CASCADE)
    option_text = models.CharField(max_length=200)
    requires_image = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category.name} - {self.option_text}"