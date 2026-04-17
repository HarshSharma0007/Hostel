from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import StudentProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    # Do nothing. Profile creation is strictly handled dynamically by pipeline.py
    # based on the domain names and Allowed databases.
    pass
