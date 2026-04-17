import secrets
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


def _generate_url_key():
    """Generate a short, URL-safe random key (8 chars)."""
    return secrets.token_urlsafe(6)[:8]


# Student Profile — enrollment_number is the primary key
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='Unknown')
    enrollment_number = models.CharField(max_length=20, primary_key=True)
    photo_url = models.URLField(blank=True)
    mobile = models.CharField(max_length=10, validators=[
        RegexValidator(
            regex=r'^\d{10}$',
            message='Enter a valid 10-digit mobile number.',
            code='invalid_mobile'
        )
    ])
    branch = models.CharField(max_length=50, blank=True, default='')
    semester = models.CharField(max_length=10, blank=True, default='')
    room_number = models.CharField(max_length=10, blank=True, default='')
    floor_number = models.CharField(max_length=10, blank=True, default='')
    assigned_hostel = models.CharField(max_length=50, blank=True, default='Hostel 1')
    first_login = models.BooleanField(default=True)

    def is_complete(self):
        return bool(self.mobile)

    def __str__(self):
        return self.user.get_full_name()


# Pre-approved student list (uploaded via CSV by warden)
class AllowedStudent(models.Model):
    email = models.EmailField(unique=True, default='test@mitsgwl.ac.in')
    added_on = models.DateTimeField(auto_now_add=True)
    enrollment_number = models.CharField(max_length=20, default='0000TEST')
    full_name = models.CharField(max_length=100, default='TEST USER')
    mobile = models.CharField(max_length=10, blank=True, default='')
    branch = models.CharField(max_length=50, default='CSE')
    semester = models.CharField(max_length=10, blank=True, default='')
    room_number = models.CharField(max_length=10, blank=True, default='')
    floor_number = models.CharField(max_length=10, blank=True, default='')
    assigned_hostel = models.CharField(max_length=50, default='Hostel 1')

    def __str__(self):
        return self.email


class FacultyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    photo_url = models.URLField(blank=True)
    first_login = models.BooleanField(default=True)

    def __str__(self):
        return self.user.get_full_name()


class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    photo_url = models.URLField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


# Warden — email is the primary key, url_key hides email in URLs
class AllowedWarden(models.Model):
    email = models.EmailField(primary_key=True)
    url_key = models.CharField(max_length=16, unique=True, default=_generate_url_key, editable=False)
    added_on = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(max_length=100)
    assigned_hostel = models.CharField(max_length=50, default='Hostel 1')

    def __str__(self):
        return self.email


class AllowedFaculty(models.Model):
    email = models.EmailField(unique=True)
    added_on = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.email
