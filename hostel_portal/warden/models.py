from django.db import models

# Create your models here.

from django.db import models

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