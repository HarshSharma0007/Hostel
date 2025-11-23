from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.models import User

from .forms import CSVUploadForm
from .models import WardenProfile

# from complaints.models import Complaint  # ✅ Uncomment when Complaint model is ready

import csv

@login_required
def warden_dashboard(request):
    email = request.user.email.lower()

    # Restrict to Gmail for now
    if not email.endswith('@gmail.com'):
        messages.error(request, "Access restricted to Gmail accounts for testing.")
        return redirect('logout')

    # Check if user has a WardenProfile
    if not hasattr(request.user, 'wardenprofile'):
        messages.error(request, "You are not authorized as a warden.")
        return redirect('logout')

    return render(request, 'warden/dashboard.html')


@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            decoded = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)

            for row in reader:
                email = row['Email']
                username = row['Enrollment Number']
                name = row['Full Name']

                user, created = User.objects.get_or_create(email=email, username=username)
                if created:
                    user.first_name = name
                    user.save()

                    send_mail(
                        'Hostel Registration',
                        'You have been added to the hostel system. Please login and complete your profile.',
                        'admin@hostel.com',
                        [email],
                        fail_silently=False,
                    )

            messages.success(request, "Students added and notified.")
            return redirect('warden_dashboard')
    else:
        form = CSVUploadForm()

    return render(request, 'warden/upload_csv.html', {'form': form})


@login_required
def complaint_list(request):
    # complaints = Complaint.objects.all().order_by('-created_at')  # ✅ Uncomment when ready
    complaints = []  # Temporary placeholder
    return render(request, 'warden/complaint_list.html', {'complaints': complaints})


from django.contrib.auth import logout
from django.shortcuts import redirect

def warden_logout_view(request):
    logout(request)
    return redirect('landing_page')  # 👈 use the name of the landing page route
