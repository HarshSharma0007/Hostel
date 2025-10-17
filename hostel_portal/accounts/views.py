# 🧑‍💻 View for students to complete their profile
from django.shortcuts import render, redirect
from .forms import ProfileEditForm
from .models import StudentProfile

def profile_edit(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('student_dashboard')  # ✅ Confirm this route exists
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})



from django.urls import reverse

# 🔗 Redirect to Google login backend
def google_login_redirect(request):
    return redirect(reverse('social:begin', args=['google-oauth2']))


def student_dashboard(request):
    profile = StudentProfile.objects.get(user=request.user)
    return render(request, 'accounts/student_dashboard.html', {'profile': profile})
