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

    summary = None

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            try:
                decoded = file.read().decode('utf-8-sig').splitlines()
                reader = list(csv.DictReader(decoded))
            except Exception:
                messages.error(request, "Invalid CSV file formatting.")
                return redirect('upload_csv')

            records_updated = 0
            records_inserted = 0
            errors = []
            
            for row_idx, row in enumerate(reader, start=2):
                email_val = row.get('Email', '').strip().lower()
                enrollment = row.get('Enrollment Number', '').strip()
                name = row.get('Full Name', '').strip()
                branch = row.get('Branch', '').strip()
                semester = row.get('Semester', '').strip()
                mobile = row.get('Mobile', '').strip()
                room = row.get('Room Number', '').strip()
                floor = row.get('Floor Number', '').strip()
                
                if not email_val and not enrollment:
                    continue
                    
                if not email_val.endswith('@mitsgwl.ac.in'):
                    errors.append({'row': row_idx, 'field': 'Email', 'message': f"Must end with @mitsgwl.ac.in"})
                    continue
                    
                if not mobile.isdigit() or len(mobile) != 10:
                    errors.append({'row': row_idx, 'field': 'Mobile', 'message': f"Must be exactly 10 digits"})
                    continue
                
                existing = AllowedStudent.objects.filter(enrollment_number=enrollment).first()
                if existing:
                    if existing.email != email_val and AllowedStudent.objects.filter(email=email_val).exists():
                        errors.append({'row': row_idx, 'field': 'Email', 'message': f"Email already in use."})
                        continue
                        
                    changed = False
                    if existing.email != email_val: changed = True; existing.email = email_val
                    if existing.full_name != name: changed = True; existing.full_name = name
                    if existing.branch != branch: changed = True; existing.branch = branch
                    if existing.semester != semester: changed = True; existing.semester = semester
                    if existing.mobile != mobile: changed = True; existing.mobile = mobile
                    if existing.room_number != room: changed = True; existing.room_number = room
                    if existing.floor_number != floor: changed = True; existing.floor_number = floor
                    
                    if changed:
                        existing.save()
                        records_updated += 1
                        
                        sp = StudentProfile.objects.filter(enrollment_number=enrollment).first()
                        if sp:
                            sp.name = name
                            sp.branch = branch
                            sp.semester = semester
                            sp.mobile = mobile
                            sp.room_number = room
                            sp.floor_number = floor
                            if getattr(sp.user, 'email', '') != email_val:
                                sp.user.email = email_val
                                sp.user.save()
                            sp.save()
                else:
                    if AllowedStudent.objects.filter(email=email_val).exists():
                        errors.append({'row': row_idx, 'field': 'Email', 'message': f"Email already in use."})
                        continue
                        
                    AllowedStudent.objects.create(
                        enrollment_number=enrollment,
                        email=email_val,
                        full_name=name,
                        branch=branch,
                        semester=semester,
                        mobile=mobile,
                        room_number=room,
                        floor_number=floor
                    )
                    records_inserted += 1
                    
            summary = {
                'updated': records_updated,
                'inserted': records_inserted,
                'errors': errors,
                'total': len(reader)
            }
    else:
        form = CSVUploadForm()

    return render(request, 'warden/upload_csv.html', {'form': form, 'summary': summary})


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

@login_required
def manage_students_view(request):
    """
    Search and list students for the Warden.
    """
    email = request.user.email.lower()
    if not email.endswith('@gmail.com'):
        return redirect('warden_logout')
    if not hasattr(request.user, 'wardenprofile'):
        return redirect('warden_logout')

    profile = request.user.wardenprofile
    q = request.GET.get('q', '').strip()
    
    # Search logic (Enrollment only as requested)
    students = []
    has_search = False
    if q:
        has_search = True
        # Look in both Profile and Allowed tables
        profiles = StudentProfile.objects.filter(enrollment_number__icontains=q)
        allowed = AllowedStudent.objects.filter(enrollment_number__icontains=q)
        
        seen_enrollments = set()
        for s in profiles:
            students.append({
                'name': s.name, 'enrollment': s.enrollment_number, 'email': s.user.email,
                'room': s.room_number, 'floor': s.floor_number, 'status': 'Active'
            })
            seen_enrollments.add(s.enrollment_number)
        for s in allowed:
            if s.enrollment_number not in seen_enrollments:
                students.append({
                    'name': s.full_name, 'enrollment': s.enrollment_number, 'email': s.email,
                    'room': s.room_number, 'floor': s.floor_number, 'status': 'Pre-approved'
                })
    else:
        # Default: list some recent students or just wait for query
        pass

    return render(request, 'warden/manage_students.html', {
        'profile': profile,
        'q': q,
        'has_search': has_search,
        'students': students
    })

@login_required
def edit_student_warden_view(request, enrollment):
    """
    Edit room/floor for a student.
    """
    email = request.user.email.lower()
    if not email.endswith('@gmail.com'):
        return redirect('warden_logout')
    if not hasattr(request.user, 'wardenprofile'):
        return redirect('warden_logout')

    profile = request.user.wardenprofile
    
    # Try to find the student in either model
    sp = StudentProfile.objects.filter(enrollment_number=enrollment).first()
    asp = AllowedStudent.objects.filter(enrollment_number=enrollment).first()
    
    if not sp and not asp:
        messages.error(request, "Student not found.")
        return redirect('manage_students')

    name = sp.name if sp else asp.full_name

    if request.method == 'POST':
        room = request.POST.get('room_number')
        floor = request.POST.get('floor_number')
        
        if sp:
            sp.room_number = room
            sp.floor_number = floor
            sp.save()
        if asp:
            asp.room_number = room
            asp.floor_number = floor
            asp.save()
            
        messages.success(request, f"Housing details updated for {name}.")
        return redirect('manage_students')

    return render(request, 'warden/edit_student.html', {
        'profile': profile,
        'enrollment': enrollment,
        'name': name,
        'student': sp or asp
    })
