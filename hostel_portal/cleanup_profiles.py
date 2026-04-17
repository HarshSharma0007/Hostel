import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_portal.settings')
django.setup()

from accounts.models import StudentProfile
from django.contrib.auth.models import User

# Identify StudentProfiles for wardens (@gmail.com)
warden_student_profiles = StudentProfile.objects.filter(user__email__endswith='@gmail.com')

print(f"Found {warden_student_profiles.count()} StudentProfiles associated with Warden accounts.")

for profile in warden_student_profiles:
    print(f"Deleting StudentProfile for {profile.user.email}")
    profile.delete()

print("Cleanup complete.")
