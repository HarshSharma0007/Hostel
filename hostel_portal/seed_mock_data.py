import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_portal.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import StudentProfile, FacultyProfile, AdminProfile, AllowedStudent, AllowedWarden, AllowedFaculty
from warden.models import WardenProfile
from complaints.models import Complaint, ComplaintCategory, CategoryField, FieldOption

def seed():
    # 1. Create Users
    admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'harsh.sharma@gmail.com'})
    student_user, _ = User.objects.get_or_create(username='0101CS221051', defaults={'email': '0101CS221051@mitsgwl.ac.in'})
    warden_user, _ = User.objects.get_or_create(username='warden_test', defaults={'email': 'warden@gmail.com'})
    faculty_user, _ = User.objects.get_or_create(username='faculty_test', defaults={'email': 'faculty@mitsgwalior.in'})


    # 2. Create Profiles
    AdminProfile.objects.get_or_create(user=admin_user, defaults={'name': 'Harsh Sharma'})
    StudentProfile.objects.get_or_create(
        enrollment_number='0101CS221051',
        user=student_user,
        defaults={
            'name': 'John Doe',
            'mobile': '9876543210',
            'branch': 'CSE',
            'semester': '4',
            'room_number': '101',
            'floor_number': '1',
            'first_login': False
        }
    )
    WardenProfile.objects.get_or_create(
        user=warden_user,
        defaults={'name': 'Mr. Smith', 'hostel_number': 'Hostel 1', 'first_login': False}
    )
    FacultyProfile.objects.get_or_create(
        user=faculty_user,
        defaults={'name': 'Dr. Brown', 'first_login': False}
    )

    # 3. Create Categories and Complaints
    cat, _ = ComplaintCategory.objects.get_or_create(name='Electricity', defaults={'description': 'Issues related to power supply'})
    cat2, _ = ComplaintCategory.objects.get_or_create(name='Water', defaults={'description': 'Leaks or supply issues'})
    
    CategoryField.objects.get_or_create(category=cat, label='Floor Number', field_type='text')
    CategoryField.objects.get_or_create(category=cat, label='Room Number', field_type='text')
    
    student_profile = StudentProfile.objects.get(enrollment_number='0101CS221051')
    Complaint.objects.get_or_create(
        student=student_profile,
        category=cat,
        defaults={'status': 'NotResolved', 'custom_title': 'Fan not working'}
    )
    Complaint.objects.get_or_create(
        student=student_profile,
        category=cat2,
        defaults={'status': 'InProgress', 'custom_title': 'Tap leak in bathroom'}
    )

    print("Mock data seeded successfully!")

if __name__ == '__main__':
    seed()
