import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_portal.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import StudentProfile, AllowedStudent
from complaints.models import Complaint, ComplaintCategory, CategoryField, ComplaintFieldValue, FieldOption
from warden.models import WardenProfile

def clear_database():
    print("🧹 Starting targeted database cleanup...")

    # 1. Clear all complaints and dynamic field values
    print("Deleting ComplaintFieldValue records...")
    ComplaintFieldValue.objects.all().delete()
    
    print("Deleting Complaint records...")
    Complaint.objects.all().delete()
    
    # 2. Clear category builder data
    print("Deleting FieldOption records...")
    FieldOption.objects.all().delete()

    print("Deleting CategoryField records...")
    CategoryField.objects.all().delete()
    
    print("Deleting ComplaintCategory records...")
    ComplaintCategory.objects.all().delete()

    # 3. Clear student profiles and allowed students list
    print("Deleting StudentProfile records...")
    StudentProfile.objects.all().delete()
    
    print("Deleting AllowedStudent records...")
    AllowedStudent.objects.all().delete()

    # 4. Clear Users but keep Wardens and Superusers
    print("Deleting non-warden Users...")
    warden_user_ids = WardenProfile.objects.values_list('user_id', flat=True)
    users_to_delete = User.objects.exclude(id__in=warden_user_ids).exclude(is_superuser=True)
    count = users_to_delete.count()
    users_to_delete.delete()
    print(f"Deleted {count} user(s).")

    print("✅ Database cleanup complete! (Wardens and Superusers preserved)")

if __name__ == "__main__":
    clear_database()
