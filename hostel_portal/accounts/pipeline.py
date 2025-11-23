
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

    if email.endswith('@mitsgwl.ac.in'):
        if not AllowedStudent.objects.filter(email=email).exists():
            print(f"[BLOCKED] {email} not in AllowedStudent")
            raise AuthForbidden(backend)

    elif email.endswith('@gmail.com'):
        print(f"✅ Gmail domain allowed: {email}")
        return

    else:
        print(f"[BLOCKED] {email} not from allowed domain")
        raise AuthForbidden(backend)


def extract_name_and_enrollment(backend, user, response, *args, **kwargs):
    email = user.email.lower()
    full_name = response.get('name', '').strip()
    photo_url = response.get('picture', '')

    if email.endswith('@mitsgwl.ac.in'):
        profile, created = StudentProfile.objects.get_or_create(user=user)

        if ' ' in full_name:
            enrollment, name = full_name.split(' ', 1)
        else:
            enrollment = ''
            name = full_name

        profile.enrollment_number = enrollment
        profile.name = name
        profile.photo_url = photo_url
        profile.first_login = created
        profile.save()

    elif email.endswith('@gmail.com'):
        profile, created = WardenProfile.objects.get_or_create(user=user)
        profile.name = full_name
        profile.photo_url = photo_url
        profile.first_login = created
        profile.save()



def redirect_after_login(strategy, user, *args, **kwargs):
    email = user.email.lower()

    if email.endswith('@mitsgwl.ac.in'):
        if not AllowedStudent.objects.filter(email=email).exists():
            print(f"[BLOCKED] {email} not in AllowedStudent")

        try:
            profile = StudentProfile.objects.get(user=user)
            if profile.first_login:
                return {'redirect_url': '/accounts/edit/'}
            else:
                return {'redirect_url': '/accounts/dashboard/'}
        except StudentProfile.DoesNotExist:
            return {'redirect_url': '/accounts/edit/'}

    elif email.endswith('@gmail.com'):
        try:
            profile = WardenProfile.objects.get(user=user)
            print("✅ Warden login")
            return {'redirect_url': '/warden/dashboard/'}
        except WardenProfile.DoesNotExist:
            print(f"⚠️ WardenProfile missing for {email} — creating now")
            WardenProfile.objects.create(user=user, first_login=True)
            return {'redirect_url': '/warden/dashboard/'}


    return {'redirect_url': '/login-error/'}

def clean_session(strategy, backend, user, request, *args, **kwargs):
    if request:
        request.session.clear()


def assign_role(strategy, details, user=None, *args, **kwargs):
    email = details.get('email', '').lower()

    if email.endswith('@mitsgwl.ac.in'):
        StudentProfile.objects.get_or_create(user=user)

    elif email.endswith('@gmail.com'):
        profile, created = WardenProfile.objects.get_or_create(user=user)
        if created:
            profile.first_login = True
            profile.save()

    else:
        raise AuthForbidden('Unrecognized domain')