# 🧑‍💻 View for students to complete their profile
from django.shortcuts import render, redirect
from .forms import ProfileEditForm
from .models import StudentProfile
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
# def profile_edit(request):
#     profile, created = StudentProfile.objects.get_or_create(user=request.user)

#     if request.method == 'POST':
#         form = ProfileEditForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect('student_dashboard')  # Confirm this route exists
#     else:
#         form = ProfileEditForm(instance=profile)

#     return render(request, 'accounts/profile_edit.html', {'form': form})

from django.shortcuts import render

def landing_page(request):
    return render(request, 'accounts/landing.html')


@login_required
def profile_edit(request):
    email = request.user.email.lower()
    
    # 🛑 CRITICAL SECURITY: Wardens (@gmail.com) should NEVER access this
    if email.endswith('@gmail.com'):
        messages.error(request, "Warden accounts cannot access student profile pages.")
        return redirect('logout')

    # Ensure user has a StudentProfile (only for @mitsgwl.ac.in)
    if not email.endswith('@mitsgwl.ac.in'):
        messages.error(request, "Access restricted to valid student accounts.")
        return redirect('logout')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile) # Added request.FILES
        if form.is_valid():
            profile = form.save(commit=False)
            profile.first_login = False
            profile.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('student_dashboard')
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form, 'profile': profile})





# 🔗 Redirect to Google login backend
def google_login_redirect(request):
    # 🛑 CRITICAL: Always logout the current user before starting a new OAuth flow. 
    # Without this, social-auth will LINK the new Google account to the 
    # currently logged-in user, causing cross-contamination between roles.
    from django.contrib.auth import logout as auth_logout
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect(reverse('social:begin', args=['google-oauth2']))

@login_required
def student_dashboard(request):
    email = request.user.email.lower()
    
    # 🛑 CRITICAL SECURITY: Wardens (@gmail.com) should NEVER access this
    if email.endswith('@gmail.com'):
        messages.error(request, "Warden accounts cannot access student dashboard.")
        return redirect('logout')

    if not email.endswith('@mitsgwl.ac.in'):
        return redirect('logout')

    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, "No student profile found for your account.")
        return redirect('logout')
    
    # 🕵️ Security Check: If profile is incomplete (no name or no mobile), force edit
    if profile.name == 'Unknown' or not profile.mobile or not profile.address:
        return redirect('profile_edit')
        
    return render(request, 'accounts/student_dashboard.html', {'profile': profile})

def login_error(request):
    return render(request, 'accounts/login_error.html')

from django.shortcuts import redirect
from accounts.models import StudentProfile
from warden.models import WardenProfile

def login_redirect_view(request):
    email = request.user.email.lower()

    # 🛑 CRITICAL SECURITY: Strictly separate routing based on email domain
    if email.endswith('@mitsgwl.ac.in'):
        try:
            profile = StudentProfile.objects.get(user=request.user)
            if profile.first_login:
                return redirect('/accounts/edit/')
            return redirect('/accounts/dashboard/')
        except StudentProfile.DoesNotExist:
            # If student is not in CSV but logged in, we still route to edit/landing to fail safely
            return redirect('/accounts/edit/')

    elif email.endswith('@gmail.com'):
        try:
            WardenProfile.objects.get(user=request.user)
            return redirect('/warden/dashboard/')
        except WardenProfile.DoesNotExist:
            WardenProfile.objects.create(user=request.user, first_login=True)
            return redirect('/warden/dashboard/')

    return redirect('/accounts/landing/')

from django.contrib.auth import logout

def custom_logout_view(request):
    logout(request)
    return redirect('landing_page')
