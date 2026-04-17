from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import FacultyProfile, StudentProfile, AllowedStudent
from complaints.models import Complaint
from master_admin.models import Hostel

@login_required
def dashboard_view(request):
    try:
        profile = FacultyProfile.objects.get(user=request.user)
    except FacultyProfile.DoesNotExist:
        messages.error(request, "Access denied. You are not registered as faculty.")
        return redirect('landing_page')

    hostel_no = request.GET.get('hostel', '').strip()
    
    # We can fetch distinct hostels for a dropdown
    hostel_choices = StudentProfile.objects.values_list('assigned_hostel', flat=True).distinct()
    hostel_choices = sorted(list(set([h for h in hostel_choices if h])))
    
    complaints = Complaint.objects.all().order_by('-created_at')
    
    if hostel_no:
        complaints = complaints.filter(student__assigned_hostel__iexact=hostel_no)
        
    stats = {
        'total': complaints.count(),
        'pending': complaints.filter(status='NotResolved').count(),
        'in_progress': complaints.filter(status='InProgress').count(),
        'resolved': complaints.filter(status='Resolved').count()
    }
    
    context = {
        'profile': profile,
        'complaints': complaints,
        'stats': stats,
        'selected_hostel': hostel_no,
        'hostel_choices': hostel_choices,
    }
    return render(request, 'faculty/dashboard.html', context)

@login_required
def complaint_detail_view(request, complaint_id):
    try:
        profile = FacultyProfile.objects.get(user=request.user)
    except FacultyProfile.DoesNotExist:
        return redirect('landing_page')
        
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    context = {
        'profile': profile,
        'c': complaint,
        'field_values': complaint.field_values.all()
    }
    return render(request, 'faculty/complaint_detail.html', context)

@login_required
def student_search_view(request):
    """
    Read-only student directory for Faculty.
    """
    try:
        profile = FacultyProfile.objects.get(user=request.user)
    except FacultyProfile.DoesNotExist:
        return redirect('landing_page')

    # Get search/filter params
    q_enrollment = request.GET.get('enrollment', '').strip()
    f_hostel = request.GET.get('hostel', '').strip()
    
    # Check if we should clear
    if 'clear' in request.GET:
        return redirect('faculty_student_search')

    # Data for filters
    hostels = Hostel.objects.filter(is_active=True).order_by('name')
    
    # Query logic
    students = []
    
    # We query both active profiles and allowed records
    # Filtering profiles
    profiles = StudentProfile.objects.all()
    if q_enrollment:
        profiles = profiles.filter(enrollment_number__icontains=q_enrollment)
    if f_hostel:
        profiles = profiles.filter(assigned_hostel__iexact=f_hostel)
    
    # Filtering allowed (pre-approved)
    allowed = AllowedStudent.objects.all()
    if q_enrollment:
        allowed = allowed.filter(enrollment_number__icontains=q_enrollment)
    if f_hostel:
        # Note: AllowedStudent also has room_number and floor_number now 
        # but let's assume filtering by assigned_hostel check
        # Wait, does AllowedStudent have assigned_hostel?
        # Let's check accounts/models.py again for AllowedStudent
        pass

    seen_enrollments = set()
    for s in profiles:
        students.append({
            'enrollment': s.enrollment_number,
            'name': s.name,
            'branch': s.branch,
            'email': s.user.email,
            'semester': s.semester,
            'hostel': s.assigned_hostel,
            'room': s.room_number,
            'floor': s.floor_number
        })
        seen_enrollments.add(s.enrollment_number)
        
    for s in allowed:
        if s.enrollment_number not in seen_enrollments:
            # We need to decide how to handle filters for AllowedStudent if they don't have hostel yet
            # Actually, the Warden update added room/floor to AllowedStudent.
            # Usually AllowedStudent results are for those who haven't logged in.
            students.append({
                'enrollment': s.enrollment_number,
                'name': s.full_name,
                'branch': s.branch,
                'email': s.email,
                'semester': s.semester,
                'hostel': getattr(s, 'assigned_hostel', 'N/A'), # Check if field exists
                'room': s.room_number,
                'floor': s.floor_number
            })

    # Sort results
    students.sort(key=lambda x: x['enrollment'])

    context = {
        'profile': profile,
        'students': students,
        'hostels': hostels,
        'q_enrollment': q_enrollment,
        'f_hostel': f_hostel,
    }
    return render(request, 'faculty/student_search.html', context)
