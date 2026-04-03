from social_core.exceptions import AuthForbidden
from django.contrib.auth import login
from django.shortcuts import redirect
from warden.models import WardenProfile
from accounts.models import StudentProfile, AllowedStudent


def auth_allowed(strategy, details, backend, user=None, *args, **kwargs):
    email = details.get('email', '').lower()
    print("🔐 Trying to authenticate:", email)

    if not email:
        raise AuthForbidden(backend)

    # 1. 👮 Warden Check - Priority 1
    # If the email is @gmail.com, it's always a Warden.
    # (Especially harshsharmaofficials@gmail.com)
    if email.endswith('@gmail.com'):
        print(f"✅ Warden domain allowed: {email}")
        return

    # 2. 🧑‍🎓 Student Check - Priority 2
    # If it's @mitsgwl.ac.in, it MUST be in AllowedStudent list
    if email.endswith('@mitsgwl.ac.in'):
        if AllowedStudent.objects.filter(email=email).exists():
            print(f"✅ Approved student domain allowed: {email}")
            return
        else:
            print(f"[BLOCKED] {email} not in AllowedStudent CSV")
            raise AuthForbidden(backend)

    # 3. 🚫 Block everyone else
    print(f"[BLOCKED] {email} not from allowed domain or not registered in CSV")
    raise AuthForbidden(backend)


def extract_name_and_enrollment(backend, user, response, *args, **kwargs):
    email = user.email.lower()
    full_name = response.get('name', '').strip()
    photo_url = response.get('picture', '')

    # 🛑 CRITICAL SECURITY: Hard-block students from ever being Wardens
    if email.endswith('@mitsgwl.ac.in'):
        # Only process as student
        is_approved_student = AllowedStudent.objects.filter(email=email).exists()
        if is_approved_student:
             # User is a STUDENT
            profile, created = StudentProfile.objects.get_or_create(user=user)
            
            # 🧪 Parse Identity from Google Name (Format: "ENROLLMENT NAME")
            google_name = response.get('name', '').strip()
            parts = google_name.split(' ', 1)
            
            if len(parts) == 2 and any(char.isdigit() for char in parts[0]):
                enrollment = parts[0]
                name = parts[1]
            else:
                email_prefix = email.split('@')[0]
                enrollment = email_prefix
                name = google_name or response.get('given_name', 'Student')

            allowed_record = AllowedStudent.objects.filter(email=email).first()
            if allowed_record:
                if not enrollment: enrollment = allowed_record.enrollment_number
                if not name or name == enrollment: name = allowed_record.full_name
                profile.branch = allowed_record.branch
                profile.semester = allowed_record.semester

            profile.enrollment_number = enrollment
            profile.name = name
            profile.photo_url = photo_url
            profile.save()
        return # Skip Warden logic for student domain
        
    elif email.endswith('@gmail.com'):
        # User is a WARDEN
        profile, created = WardenProfile.objects.get_or_create(user=user)
        if created:
            profile.name = full_name
            profile.photo_url = photo_url
            profile.first_login = True
            profile.save()


def redirect_after_login(strategy, user, *args, **kwargs):
    email = user.email.lower()

    # 🛑 CRITICAL SECURITY: Always route student domain to student pages
    if email.endswith('@mitsgwl.ac.in'):
        is_approved_student = AllowedStudent.objects.filter(email=email).exists()
        if is_approved_student:
            try:
                profile = StudentProfile.objects.get(user=user)
                if profile.first_login:
                    return {'redirect_url': '/accounts/edit/'}
                return {'redirect_url': '/accounts/dashboard/'}
            except StudentProfile.DoesNotExist:
                return {'redirect_url': '/accounts/edit/'}
        else:
            return {'redirect_url': '/login-error/'}
            
    elif email.endswith('@gmail.com'):
        return {'redirect_url': '/warden/dashboard/'}

    return {'redirect_url': '/login-error/'}


def assign_role(strategy, details, user=None, *args, **kwargs):
    """
    Ensure the profile records exist correctly at the end of the pipeline.
    """
    email = details.get('email', '').lower()

    if email.endswith('@mitsgwl.ac.in'):
        # Only ever create StudentProfile for student domain
        is_approved_student = AllowedStudent.objects.filter(email=email).exists()
        if is_approved_student:
            StudentProfile.objects.get_or_create(user=user)
        return

    elif email.endswith('@gmail.com'):
        WardenProfile.objects.get_or_create(
            user=user,
            defaults={
                'name': details.get('fullname', '') or user.get_full_name(),
                'first_login': True,
            }
        )
