from django.shortcuts import render, redirect
from .forms import ProfileEditForm
from .models import StudentProfile, FacultyProfile, AdminProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse
from warden.models import WardenProfile
from django.conf import settings


# ADMIN_EMAILS list is now managed via .env and settings.py



def landing_page(request):
    """
    Landing page with inline error handling.
    Accepts ?error=unauthorized or ?error=server as query params.
    """
    error_type = request.GET.get('error', '')
    return render(request, 'accounts/landing.html', {'error_type': error_type})


@login_required
def profile_edit(request):
    email = request.user.email.lower()

    # SECURITY: Non-students should NEVER access this
    if not email.endswith('@mitsgwl.ac.in'):
        return redirect('logout')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.first_login = False
            profile.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('student_dashboard')
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form, 'profile': profile})


def google_login_redirect(request):
    """
    Redirect to Google OAuth. Always logout first to prevent
    social-auth from linking a new Google account to a stale session.
    """
    from django.contrib.auth import logout as auth_logout
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect(reverse('social:begin', args=['google-oauth2']))


@login_required
def student_dashboard(request):
    email = request.user.email.lower()

    # SECURITY: Only students can access this
    if not email.endswith('@mitsgwl.ac.in'):
        return redirect('logout')

    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, "No student profile found for your account.")
        return redirect('logout')

    # If profile is incomplete, force edit
    if profile.name == 'Unknown' or not profile.mobile:
        return redirect('profile_edit')

    return render(request, 'accounts/student_dashboard.html', {'profile': profile})


def login_redirect_view(request):
    """
    Post-login redirect router. Routes authenticated users to
    their correct dashboard based on email and profile.
    Fully database-safe — will never crash on missing tables/columns.
    """
    import logging
    logger = logging.getLogger(__name__)
    email = request.user.email.lower()

    try:
        # Student
        if email.endswith('@mitsgwl.ac.in'):
            try:
                profile = StudentProfile.objects.get(user=request.user)
                if profile.first_login:
                    return redirect('/accounts/edit/')
                return redirect('/accounts/dashboard/')
            except StudentProfile.DoesNotExist:
                return redirect('/accounts/edit/')

        # --- TEST USERS (Bypasses regular domain checks) ---
        if settings.TEST_WARDEN_EMAIL and email == settings.TEST_WARDEN_EMAIL:
            # Sync role exclusivity
            FacultyProfile.objects.filter(user=request.user).delete()
            if not WardenProfile.objects.filter(user=request.user).exists():
                WardenProfile.objects.create(user=request.user, name=settings.TEST_WARDEN_NAME, hostel_number=settings.TEST_WARDEN_HOSTEL, first_login=False)
            return redirect('/warden/dashboard/')

        if settings.TEST_FACULTY_EMAIL and email == settings.TEST_FACULTY_EMAIL:
            # Sync role exclusivity
            WardenProfile.objects.filter(user=request.user).delete()
            if not FacultyProfile.objects.filter(user=request.user).exists():
                FacultyProfile.objects.create(user=request.user, name=settings.TEST_FACULTY_NAME, first_login=False)
            return redirect('/faculty/dashboard/')

        # Admin
        if email in settings.ADMIN_EMAILS:

            try:
                AdminProfile.objects.get(user=request.user)
            except AdminProfile.DoesNotExist:
                AdminProfile.objects.create(user=request.user)
            return redirect('/master-admin/dashboard/')
        else:
            # Security: If they have an AdminProfile but are NOT in the list, revoke it.
            if AdminProfile.objects.filter(user=request.user).exists():
                AdminProfile.objects.filter(user=request.user).delete()
                logger.warning(f"[ACCESS DENIED] Revoked admin access for {email}")
                logout(request)
                return redirect('/?error=unauthorized')

        # Faculty
        if email.endswith('@mitsgwalior.in'):
            try:
                FacultyProfile.objects.get(user=request.user)
                return redirect('/faculty/dashboard/')
            except FacultyProfile.DoesNotExist:
                FacultyProfile.objects.create(user=request.user, first_login=True)
                return redirect('/faculty/dashboard/')

        # Warden (Gmail)
        if email.endswith('@gmail.com'):
            try:
                WardenProfile.objects.get(user=request.user)
                return redirect('/warden/dashboard/')
            except WardenProfile.DoesNotExist:
                WardenProfile.objects.create(user=request.user, first_login=True)
                return redirect('/warden/dashboard/')

    except Exception as e:
        # Catches ProgrammingError, OperationalError (missing tables/columns)
        logger.error(f"[LOGIN REDIRECT DB ERROR] {type(e).__name__}: {e}")
        logout(request)
        return redirect('/?error=server')

    # Unknown — logout and send to landing with error
    logout(request)
    return redirect('/?error=unauthorized')


def custom_logout_view(request):
    logout(request)
    return redirect('landing_page')


def custom_404_view(request, exception=None):
    """
    Redirects unauthenticated users to landing,
    and authenticated users to their correct dashboard.
    """
    if not request.user.is_authenticated:
        return redirect('/?error=notfound')
    
    # Use existing router logic
    return login_redirect_view(request)


def custom_500_view(request):
    """
    Redirects to landing page with server error message.
    """
    return redirect('/?error=server')

