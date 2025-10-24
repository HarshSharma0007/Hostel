
from social_core.exceptions import AuthForbidden
from accounts.models import AllowedStudent
from django.contrib.auth import login
from accounts.models import StudentProfile 

from django.shortcuts import redirect
from accounts.models import StudentProfile


# def auth_allowed(strategy, details, user=None, *args, **kwargs):
#     email = details.get('email')
#     backend = kwargs.get('backend')  # ✅ Correct way to access backend

#     if not AllowedStudent.objects.filter(email=email).exists():
#         raise AuthForbidden(backend)  # ✅ Use backend from kwargs




# def auth_allowed(strategy, details, user=None, *args, **kwargs):
#     email = details.get('email')
#     backend = kwargs.get('backend')

#     if not AllowedStudent.objects.filter(email=email).exists():
#         print(f"[AUTH BLOCKED] {email} is not in AllowedStudent")
#         raise AuthForbidden(backend)

# def auth_allowed(strategy, details, backend, user=None, *args, **kwargs):
#     email = details.get('email')
#     if not email:
#         raise AuthForbidden(backend)

#     if (
#         not AllowedStudent.objects.filter(email=email).exists()
#         # and not WardenProfile.objects.filter(user__email=email).exists()
#         # and not FacultyProfile.objects.filter(user__email=email).exists()
#     ):
#         print(f"[AUTH BLOCKED] {email} is not in Allowed.")
#         raise AuthForbidden(backend)


def auth_allowed(strategy, details, backend, user=None, *args, **kwargs):
    email = details.get('email')
    print("Trying to authenticate:", email)  # ✅ Add this for debug
    if not email:
        raise AuthForbidden(backend)

    if not AllowedStudent.objects.filter(email=email).exists():
        raise AuthForbidden(backend)


def extract_name_and_enrollment(backend, user, response, *args, **kwargs):
    

    profile, _ = StudentProfile.objects.get_or_create(user=user)

    # Example: "0901AM231031 Kavya Jain"
    full_name = response.get('name', '').strip()

    # Extract enrollment number and name from full_name
    if ' ' in full_name:
        enrollment, name = full_name.split(' ', 1)
    else:
        enrollment = ''
        name = full_name

    # Optional: Extract Google profile photo
    photo_url = response.get('picture', '')

    profile.enrollment_number = enrollment
    profile.name = name
    profile.photo_url = photo_url
    profile.save()



def redirect_after_login(strategy, user, *args, **kwargs):
    request = strategy.request
    print("➡️ redirect_after_login: user =", user.email, "| is_authenticated =", request.user.is_authenticated)
    profile = StudentProfile.objects.get(user=user)
    if profile.is_complete():
        return redirect('student_dashboard')
    else:
        return redirect('profile_edit')


def clean_session(strategy, backend, user, request, *args, **kwargs):
    if request:
        request.session.clear()


from django.contrib.auth import login


def assign_role(backend, user, request, *args, **kwargs):
    print("✅ assign_role called for:", user.email)

    # ✅ Explicitly set backend to avoid ValueError
    user.backend = 'social_core.backends.google.GoogleOAuth2'

    print("Session before login:", request.session.session_key)
    login(request, user)
    print("Session after login:", request.session.session_key)
    print("✅ User logged in:", request.user.is_authenticated)
