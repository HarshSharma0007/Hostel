# 🧑‍💻 View for students to complete their profile
from django.shortcuts import render, redirect
from .forms import ProfileEditForm
from .models import StudentProfile
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profile updated successfully.")
            return redirect('student_dashboard')
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form,
                                                          'profile': profile})



from django.urls import reverse

# 🔗 Redirect to Google login backend
def google_login_redirect(request):
    return redirect(reverse('social:begin', args=['google-oauth2']))

@login_required
def student_dashboard(request):
    profile = StudentProfile.objects.get(user=request.user)
    return render(request, 'accounts/student_dashboard.html', {'profile': profile})

def login_error(request):
    return render(request, 'accounts/login_error.html')
