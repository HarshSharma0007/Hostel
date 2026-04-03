from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.models import User

from .forms import CSVUploadForm
from .models import WardenProfile
from accounts.models import StudentProfile, AllowedStudent

from complaints.models import Complaint, ComplaintFieldValue


import csv

@login_required
def warden_dashboard(request):
    email = request.user.email.lower()

    # 🛑 CRITICAL SECURITY: Only @gmail.com can ever be a Warden
    if not email.endswith('@gmail.com'):
        messages.error(request, "Access restricted to Warden accounts.")
        return redirect('logout')

    # Check if user has a WardenProfile
    if not hasattr(request.user, 'wardenprofile'):
        messages.error(request, "You are not authorized as a warden.")
        return redirect('logout')

    profile = request.user.wardenprofile
    
    # 📊 Aggregate complaint statistics (Removing Invalid)
    all_complaints = Complaint.objects.all()
    stats = {
        'total': all_complaints.exclude(status='Invalid').count(),
        'pending': all_complaints.filter(status='NotResolved').count(),
        'in_progress': all_complaints.filter(status='InProgress').count(),
        'resolved': all_complaints.filter(status='Resolved').count(),
    }
    
    # Get unresolved complaints (Pending + In Progress)
    unresolved_complaints = all_complaints.filter(status__in=['NotResolved', 'InProgress']).order_by('-created_at')

    return render(request, 'warden/dashboard.html', {
        'profile': profile,
        'stats': stats,
        'unresolved_complaints': unresolved_complaints
    })

@login_required
def email_center(request):
    """
    Dedicated view for the Warden to compose and send messages to students.
    """
    email = request.user.email.lower()
    if not email.endswith('@gmail.com'):
        return redirect('logout')

    if not hasattr(request.user, 'wardenprofile'):
        return redirect('logout')
        
    students = AllowedStudent.objects.all().order_by('full_name')
    
    if request.method == 'POST':
        target = request.POST.get('target') # 'all' or specific email
        subject = request.POST.get('subject')
        message_body = request.POST.get('message_body')
        
        recipient_list = []
        if target == 'all':
            recipient_list = list(students.values_list('email', flat=True))
        else:
            recipient_list = [target]
            
        try:
            send_mail(
                subject,
                message_body,
                'admin@hostel.com',
                recipient_list,
                fail_silently=False,
            )
            messages.success(request, f"🚀 Message successfully sent to {len(recipient_list)} recipient(s)!")
            return redirect('warden_dashboard')
        except Exception as e:
            messages.error(request, f"❌ Failed to send message: {str(e)}")
            
    return render(request, 'warden/email_compose.html', {'students': students})


@login_required
def upload_csv(request):
    email = request.user.email.lower()
    if not email.endswith('@gmail.com'):
        return redirect('logout')

    if not hasattr(request.user, 'wardenprofile'):
        messages.error(request, "Access restricted to wardens.")
        return redirect('logout')

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            try:
                decoded = file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded)
            except Exception:
                messages.error(request, "Invalid CSV file formatting.")
                return redirect('upload_csv')

            preview_data = []
            
            # Fetch existing emails to flag duplicates during preview
            existing_emails = set(AllowedStudent.objects.values_list('email', flat=True))

            for row in reader:
                email = row.get('Email', '').strip()
                enrollment = row.get('Enrollment Number', '').strip()
                name = row.get('Full Name', '').strip()
                branch = row.get('Branch', '').strip()
                semester = row.get('Semester', '').strip()

                if not email or not enrollment or not name:
                    continue # Skip empty rows

                is_duplicate = email in existing_emails
                
                preview_data.append({
                    'email': email,
                    'enrollment': enrollment,
                    'name': name,
                    'branch': branch,
                    'semester': semester,
                    'is_duplicate': is_duplicate
                })

            # Save the preview to the session to be processed upon confirmation
            request.session['csv_preview_data'] = preview_data
            
            return render(request, 'warden/upload_csv_preview.html', {
                'preview_data': preview_data,
                'total_rows': len(preview_data),
                'total_duplicates': sum(1 for row in preview_data if row['is_duplicate'])
            })
    else:
        form = CSVUploadForm()

    return render(request, 'warden/upload_csv.html', {'form': form})

@login_required
def confirm_csv_upload(request):
    email = request.user.email.lower()
    if not email.endswith('@gmail.com'):
        return redirect('logout')

    if not hasattr(request.user, 'wardenprofile'):
        return redirect('logout')
        
    if request.method == 'POST':
        preview_data = request.session.get('csv_preview_data', [])
        if not preview_data:
            messages.error(request, "Session expired or no data found. Please re-upload the CSV.")
            return redirect('upload_csv')
            
        added_count = 0
        
        for row in preview_data:
            email = row['email']
            enrollment = row['enrollment']
            name = row['name']
            branch = row['branch']
            semester = row['semester']

            # Save to AllowedStudent
            AllowedStudent.objects.update_or_create(
                email=email,
                defaults={
                    'enrollment_number': enrollment,
                    'full_name': name,
                    'branch': branch,
                    'semester': semester,
                }
            )

            # Create Django user if not exists
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': enrollment}
            )
            if created:
                user.first_name = name
                user.save()
                added_count += 1

            # Create/update StudentProfile with warden-assigned fields
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            profile.name = name
            profile.enrollment_number = enrollment
            profile.branch = branch
            profile.semester = semester
            profile.save()

            if created:
                try:
                    send_mail(
                        'Hostel Registration',
                        f'Hello {name},\n\nYou have been added to the hostel system. '
                        f'Please login and complete your profile.\n\nEnrollment: {enrollment}',
                        'admin@hostel.com',
                        [email],
                        fail_silently=True,
                    )
                except Exception:
                    pass  # Don't block upload if email fails

        # Clear session
        if 'csv_preview_data' in request.session:
            del request.session['csv_preview_data']

        messages.success(request, f"Successfully processed {len(preview_data)} students. ({added_count} new accounts created).")
        return redirect('warden_dashboard')
        
    return redirect('upload_csv')


@login_required
def complaint_list(request):
    email = request.user.email.lower()
    if not email.endswith('@gmail.com'):
        return redirect('logout')

    if not hasattr(request.user, 'wardenprofile'):
        return redirect('logout')
        
    complaints = Complaint.objects.all().order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
        
    return render(request, 'warden/complaint_list.html', {'complaints': complaints, 'current_status': status_filter})

@login_required
def complaint_detail(request, pk):
    email = request.user.email.lower()
    if not email.endswith('@gmail.com'):
        return redirect('logout')

    if not hasattr(request.user, 'wardenprofile'):
        return redirect('logout')
        
    complaint = Complaint.objects.get(pk=pk)
    answers = complaint.field_values.all()
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Complaint.STATUS_CHOICES):
            complaint.status = new_status
            complaint.save()
            messages.success(request, f"Complaint status updated to {complaint.get_status_display()}")
            return redirect('complaint_detail', pk=pk)
            
    return render(request, 'warden/complaint_detail.html', {'complaint': complaint, 'answers': answers})


from django.contrib.auth import logout
from django.shortcuts import redirect

def warden_logout_view(request):
    logout(request)
    return redirect('landing_page')  # 👈 use the name of the landing page route

@login_required
def send_invitations(request):
    """
    Sends an invitation email to all pre-approved students who haven't logged in yet.
    """
    email = request.user.email.lower()
    if not email.endswith('@gmail.com'):
        return redirect('logout')

    if not hasattr(request.user, 'wardenprofile'):
        return redirect('logout')

    # Find students in AllowedStudent who don't have a StudentProfile yet 
    # (meaning they haven't logged in for the first time)
    existing_profile_emails = StudentProfile.objects.values_list('user__email', flat=True)
    students_to_invite = AllowedStudent.objects.exclude(email__in=existing_profile_emails)

    sent_count = 0
    fail_count = 0

    for student in students_to_invite:
        try:
            send_mail(
                'Invitation: Join the Hostel Portal',
                f"Hello {student.full_name},\n\n"
                f"You have been pre-approved for the new Hostel Complaint Portal.\n"
                f"Please log in using your college email to complete your registration and profile.\n\n"
                f"Login here: {request.build_absolute_uri('/')}\n\n"
                f"Enrollment Number: {student.enrollment_number}\n\n"
                f"Best regards,\nHostel Administration",
                'admin@hostel.com',
                [student.email],
                fail_silently=False,
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to send email to {student.email}: {e}")
            fail_count += 1

    if sent_count > 0:
        messages.success(request, f"🚀 Successfully sent {sent_count} invitations!")
    if fail_count > 0:
        messages.warning(request, f"⚠️ Failed to send {fail_count} invitations. Check server logs.")
    if sent_count == 0 and fail_count == 0:
        messages.info(request, "All pre-approved students have already joined!")

    return redirect('warden_dashboard')
