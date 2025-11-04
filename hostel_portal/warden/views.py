from django.shortcuts import render

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def warden_dashboard(request):
    # Restrict to college domain
    if not request.user.email.endswith('@mitsgwalior.in'):
        messages.error(request, "Access restricted to college domain.")
        return redirect('logout')

    # Check if user is marked as warden
    if not hasattr(request.user, 'profile') or not request.user.profile.is_warden:
        messages.error(request, "You are not authorized as a warden.")
        return redirect('logout')

    return render(request, 'warden/dashboard.html')

import csv
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .forms import CSVUploadForm

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

                    # Send email notification
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

from accounts.models import Complaint

@login_required
def complaint_list(request):
    complaints = Complaint.objects.all().order_by('-created_at')
    return render(request, 'warden/complaint_list.html', {'complaints': complaints})