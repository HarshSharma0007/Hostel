from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator



# 🧑‍🎓 Each student has a profile linked to their Django user
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


    name = models.CharField(max_length=100, default='Unknown')

    # 🎓 Extracted from email username (e.g. 2021XXXX@college.edu)
    enrollment_number = models.CharField(max_length=20)

    # 🖼️ Google profile photo URL
    photo_url = models.URLField(blank=True)

    # 📱 Contact details
    mobile = models.CharField(max_length=10, validators=[
                    RegexValidator(
                        regex=r'^\d{10}$',
                        message='Enter a valid 10-digit mobile number.',
                        code='invalid_mobile'
                    )
                ])

    parent_mobile = models.CharField(max_length=10, validators=[
                    RegexValidator(
                        regex=r'^\d{10}$',
                        message='Enter a valid 10-digit mobile number.',
                        code='invalid_mobile'
                    )
                ])
    alt_parent_mobile = models.CharField(max_length=10, validators=[
                    RegexValidator(
                        regex=r'^\d{10}$',
                        message='Enter a valid 10-digit mobile number.',
                        code='invalid_mobile'
                    )
                ], blank=True)

    # 🎓 Warden-assigned fields (not editable by student)
    branch = models.CharField(max_length=50, blank=True, default='')
    semester = models.CharField(max_length=10, blank=True, default='')
    room_number = models.CharField(max_length=10, blank=True, default='')
    floor_number = models.CharField(max_length=10, blank=True, default='')
    assigned_hostel = models.CharField(max_length=50, blank=True, default='Hostel 1')

    # 🏠 Address fields
    address = models.TextField()
    city = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=10)
    state = models.CharField(max_length=50)
    first_login = models.BooleanField(default=True)

    def is_complete(self):
        required_fields = [
            self.mobile,
            self.parent_mobile,
            self.address,
            self.city,
            self.pin_code,
            self.state,
        ]
        return all(required_fields)

    def __str__(self):
        return self.user.get_full_name()  # For admin/debug display

class AllowedStudent(models.Model):
    email = models.EmailField(unique=True, default='test@mitsgwl.ac.in')
    added_on = models.DateTimeField(auto_now_add=True)  # No default needed
    enrollment_number = models.CharField(max_length=20, default='0000TEST')
    full_name = models.CharField(max_length=100, default='TEST USER')
    branch = models.CharField(max_length=50, default='CSE')
    semester = models.CharField(max_length=10, blank=True, default='')
    room_number = models.CharField(max_length=10, blank=True, default='')
    floor_number = models.CharField(max_length=10, blank=True, default='')
    assigned_hostel = models.CharField(max_length=50, default='Hostel 1')
