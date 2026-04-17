import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import AdminProfile, StudentProfile, FacultyProfile, AllowedWarden, AllowedFaculty, AllowedStudent
from warden.models import WardenProfile
from complaints.models import Complaint
from django.http import JsonResponse
from .models import Hostel, Floor, Room


def get_admin_profile(request):
    try:
        return AdminProfile.objects.get(user=request.user)
    except AdminProfile.DoesNotExist:
        return None

@login_required
def dashboard_view(request):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')

    total_hostels = Hostel.objects.count()

    recent_students = StudentProfile.objects.all().order_by('-user__date_joined')[:5]

    stats = {
        'students': AllowedStudent.objects.count(),
        'wardens': AllowedWarden.objects.count(),
        'faculty': AllowedFaculty.objects.count(),
        'complaints_total': Complaint.objects.count(),
        'complaints_pending': Complaint.objects.filter(status='NotResolved').count(),
        'total_hostels': total_hostels,
    }
    return render(request, 'master_admin/dashboard.html', {'profile': profile, 'stats': stats, 'recent_students': recent_students})

@login_required
def search_users_view(request):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')

    q = request.GET.get('q', '').strip()
    roles = request.GET.getlist('roles')
    hostel = request.GET.get('hostel', '').strip()
    enrollment = request.GET.get('enrollment', '').strip()
    email = request.GET.get('email', '').strip()
    exact_match = request.GET.get('exact_enrollment') == 'on'

    # 1. Fetch all relevant models
    all_profiles_students = StudentProfile.objects.all()
    all_allowed_students = AllowedStudent.objects.all()
    
    all_profiles_wardens = WardenProfile.objects.all()
    all_allowed_wardens = AllowedWarden.objects.all()
    
    all_profiles_faculty = FacultyProfile.objects.all()
    all_allowed_faculty = AllowedFaculty.objects.all()

    has_search = any([q, roles, hostel, enrollment, email])

    found_students = []
    found_wardens = []
    found_faculty = []

    if has_search:
        # Search Students
        s_prof = all_profiles_students
        s_allo = all_allowed_students
        if q:
            s_prof = s_prof.filter(name__icontains=q) | s_prof.filter(enrollment_number__icontains=q) | s_prof.filter(room_number__icontains=q) | s_prof.filter(user__email__icontains=q)
            s_allo = s_allo.filter(full_name__icontains=q) | s_allo.filter(enrollment_number__icontains=q) | s_allo.filter(email__icontains=q)
        if enrollment:
            if exact_match:
                s_prof = s_prof.filter(enrollment_number=enrollment)
                s_allo = s_allo.filter(enrollment_number=enrollment)
            else:
                s_prof = s_prof.filter(enrollment_number__icontains=enrollment)
                s_allo = s_allo.filter(enrollment_number__icontains=enrollment)
        if email:
            s_prof = s_prof.filter(user__email__icontains=email)
            s_allo = s_allo.filter(email__icontains=email)
        if hostel:
            s_prof = s_prof.filter(assigned_hostel__icontains=hostel)
            s_allo = s_allo.filter(assigned_hostel__icontains=hostel)

        # Search Wardens
        w_prof = all_profiles_wardens
        w_allo = all_allowed_wardens
        if q:
            w_prof = w_prof.filter(name__icontains=q) | w_prof.filter(user__email__icontains=q) | w_prof.filter(hostel_number__icontains=q)
            w_allo = w_allo.filter(full_name__icontains=q) | w_allo.filter(email__icontains=q) | w_allo.filter(assigned_hostel__icontains=q)
        if email:
            w_prof = w_prof.filter(user__email__icontains=email)
            w_allo = w_allo.filter(email__icontains=email)
        if hostel:
            w_prof = w_prof.filter(hostel_number__icontains=hostel)
            w_allo = w_allo.filter(assigned_hostel__icontains=hostel)

        # Search Faculty
        f_prof = all_profiles_faculty
        f_allo = all_allowed_faculty
        if q:
            f_prof = f_prof.filter(name__icontains=q) | f_prof.filter(user__email__icontains=q)
            f_allo = f_allo.filter(full_name__icontains=q) | f_allo.filter(email__icontains=q)
        if email:
            f_prof = f_prof.filter(user__email__icontains=email)
            f_allo = f_allo.filter(email__icontains=email)
        if hostel:
            # Faculty don't have hostels
            f_prof = f_prof.none()
            f_allo = f_allo.none()

        # Combine and Unify
        if not roles or 'student' in roles:
            seen_students = set()
            for s in s_prof:
                found_students.append({
                    'name': s.name, 'enrollment': s.enrollment_number, 'email': s.user.email,
                    'hostel': s.assigned_hostel, 'room': s.room_number, 'status': 'Active',
                    'edit_url_id': s.enrollment_number
                })
                seen_students.add(s.enrollment_number)
            for s in s_allo:
                if s.enrollment_number not in seen_students:
                    found_students.append({
                        'name': s.full_name, 'enrollment': s.enrollment_number, 'email': s.email,
                        'hostel': s.assigned_hostel, 'room': s.room_number or 'N/A', 'status': 'Pre-approved',
                        'edit_url_id': s.enrollment_number
                    })

        if not roles or 'warden' in roles:
            # Get mapping for url_keys
            key_map = {aw.email.lower(): aw.url_key for aw in all_allowed_wardens}
            seen_wardens = set()
            for w in w_prof:
                email_lower = w.user.email.lower()
                found_wardens.append({
                    'id': w.id, 'name': w.name, 'email': w.user.email,
                    'hostel': w.hostel_number, 'status': 'Active',
                    'url_key': key_map.get(email_lower, 'none')
                })
                seen_wardens.add(email_lower)
            for w in w_allo:
                email_lower = w.email.lower()
                if email_lower not in seen_wardens:
                    found_wardens.append({
                        'id': 'Pre-app', 'name': w.full_name, 'email': w.email,
                        'hostel': w.assigned_hostel, 'status': 'Pre-approved',
                        'url_key': w.url_key
                    })

        if not roles or 'faculty' in roles:
            seen_faculty = set()
            for f in f_prof:
                email_lower = f.user.email.lower()
                found_faculty.append({
                    'id': f.id, 'name': f.name, 'email': f.user.email, 'status': 'Active'
                })
                seen_faculty.add(email_lower)
            for f in f_allo:
                email_lower = f.email.lower()
                if email_lower not in seen_faculty:
                    found_faculty.append({
                        'id': 'Pre-app', 'name': f.full_name, 'email': f.email, 'status': 'Pre-approved'
                    })

    # get distinct hostels for the dropdown
    student_hostels = set(StudentProfile.objects.exclude(assigned_hostel='').values_list('assigned_hostel', flat=True))
    warden_hostels = set(WardenProfile.objects.exclude(hostel_number='').values_list('hostel_number', flat=True))
    all_hostels = sorted(list(student_hostels.union(warden_hostels)))

    return render(request, 'master_admin/search.html', {
        'profile': profile,
        'q': q,
        'roles': roles,
        'hostel': hostel,
        'enrollment': enrollment,
        'email': email,
        'exact_enrollment': exact_match,
        'all_hostels': all_hostels,
        'has_search': has_search,
        'students': found_students, 'wardens': found_wardens, 'faculty': found_faculty
    })

@login_required
def manage_staff_view(request):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_manual':
            role = request.POST.get('role')
            email = request.POST.get('email').lower()
            name = request.POST.get('name')
            extra = request.POST.get('extra', '') # hostel or department
            if not email.endswith('@mitsgwalior.in'):
                messages.error(request, "Email must end with @mitsgwalior.in")
            else:
                if role == 'warden':
                    AllowedWarden.objects.update_or_create(email=email, defaults={'full_name': name, 'assigned_hostel': extra})
                    messages.success(request, f"Warden {email} pre-approved successfully.")
                elif role == 'faculty':
                    AllowedFaculty.objects.update_or_create(email=email, defaults={'full_name': name})
                    messages.success(request, f"Faculty {email} pre-approved successfully.")
            
        elif action == 'upload_csv':
            role = request.POST.get('csv_role')
            file = request.FILES.get('csv_file')
            if file:
                try:
                    decoded = file.read().decode('utf-8-sig').splitlines()
                    reader = csv.DictReader(decoded)
                    count = 0
                    row_idx = 1
                    for row in reader:
                        row_idx += 1
                        email = row.get('Email', '').strip().lower()
                        name = row.get('Name', '').strip()
                        extra = row.get('Hostel', '').strip() if role == 'warden' else row.get('Extra', '').strip()
                        
                        if not email:
                            continue
                            
                        if not email.endswith('@mitsgwalior.in'):
                            messages.error(request, f"Row {row_idx}: Email '{email}' must end with @mitsgwalior.in")
                            continue

                        if role == 'warden':
                            # Validate hostel exists and is active
                            hostel_obj = Hostel.objects.filter(name=extra, is_active=True).first()
                            if not hostel_obj:
                                messages.error(request, f"tell the wrong hostel in csv NOT EXIST: '{extra}' (Row {row_idx})")
                                return redirect('admin_manage_staff')

                            AllowedWarden.objects.update_or_create(email=email, defaults={'full_name': name, 'assigned_hostel': extra})
                            count += 1
                        elif role == 'faculty':
                            # Faculty CSV no longer expects 'extra' (Department)
                            AllowedFaculty.objects.update_or_create(email=email, defaults={'full_name': name})
                            count += 1
                    messages.success(request, f"Successfully processed {count} {role} emails from CSV.")
                except Exception as e:
                    messages.error(request, f"Invalid CSV file: Ensure headers are Exact (Email, Name, Hostel/Extra). Reason: {str(e)}")

        return redirect('admin_manage_staff')

    return render(request, 'master_admin/manage_staff.html', {
        'profile': profile,
        'allowed_wardens': AllowedWarden.objects.all(),
        'allowed_faculty': AllowedFaculty.objects.all(),
        'hostels': Hostel.objects.filter(is_active=True),
    })

@login_required
def complaint_manager_view(request):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')

    complaints = Complaint.objects.all().order_by('-created_at')
    status = request.GET.get('status')
    if status:
        complaints = complaints.filter(status=status)

    return render(request, 'master_admin/complaints.html', {'profile': profile, 'complaints': complaints, 'status': status})

@login_required
def edit_student_view(request, student_id):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')
    s = get_object_or_404(StudentProfile, enrollment_number=student_id)
    
    if request.method == 'POST':
        s.name = request.POST.get('name')
        s.room_number = request.POST.get('room_number')
        s.assigned_hostel = request.POST.get('assigned_hostel')
        s.mobile = request.POST.get('mobile')
        s.save()
        messages.success(request, f"Student {s.name} manually updated.")
        return redirect('admin_search_users')
        
    return render(request, 'master_admin/edit_student.html', {'profile': profile, 's': s})

@login_required
def edit_faculty_view(request, faculty_id):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')
    f = get_object_or_404(FacultyProfile, id=faculty_id)
    if request.method == 'POST':
        f.name = request.POST.get('name')
        f.save()
        messages.success(request, "Faculty member updated.")
        return redirect('admin_search_users')
    return render(request, 'master_admin/edit_staff.html', {'profile': profile, 'staff': f, 'type': 'Faculty'})

@login_required
def edit_warden_view(request, warden_key):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')
    
    # Look up the AllowedWarden by url_key, then find the WardenProfile via email
    aw = get_object_or_404(AllowedWarden, url_key=warden_key)
    w = WardenProfile.objects.filter(user__email=aw.email).first()
    
    if request.method == 'POST':
        new_name = request.POST.get('name', '')
        new_hostel = request.POST.get('hostel_number', '')
        
        # Update WardenProfile if it exists
        if w:
            w.name = new_name
            w.hostel_number = new_hostel
            w.save()
        
        # Always sync back to AllowedWarden
        aw.full_name = new_name
        aw.assigned_hostel = new_hostel
        aw.save()
        
        messages.success(request, "Warden details updated.")
        return redirect('admin_search_users')
        
    return render(request, 'master_admin/edit_staff.html', {
        'profile': profile, 
        'staff': w or aw,  # Show WardenProfile if exists, else AllowedWarden
        'warden_record': aw,
        'type': 'Warden',
        'hostels': Hostel.objects.all(),
    })


@login_required
def edit_complaint_view(request, complaint_id):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')
    c = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            c.delete()
            messages.success(request, f"Complaint {c.ticket_number} completely erased.")
            return redirect('admin_complaint_manager')
        else:
            c.status = request.POST.get('status')
            c.save()
            messages.success(request, f"Complaint {c.ticket_number} status overridden to {c.status}.")
            return redirect('admin_complaint_manager')
        
    return render(request, 'master_admin/edit_complaint.html', {'profile': profile, 'c': c, 'answers': c.field_values.all()})



@login_required
def admin_hostel_dashboard(request):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_hostel':
            name = request.POST.get('hostel_name', '').strip()
            if name:
                if Hostel.objects.filter(name=name).exists():
                    messages.error(request, f"Hostel '{name}' already exists.")
                else:
                    Hostel.objects.create(name=name)
                    messages.success(request, f"Hostel '{name}' created successfully.")
            else:
                messages.error(request, "Hostel name cannot be empty.")
            return redirect('admin_hostel_dashboard')
        elif action == 'toggle_status':
            hid = request.POST.get('hostel_id')
            h = get_object_or_404(Hostel, id=hid)
            h.is_active = not h.is_active
            h.save()
            messages.success(request, f"Status for '{h.name}' toggled.")
            return redirect('admin_hostel_dashboard')

    hostels = Hostel.objects.all().order_by('name')
    return render(request, 'master_admin/hostel_dashboard.html', {'profile': profile, 'hostels': hostels})

@login_required
def admin_floor_dashboard(request, hostel_id):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')

    hostel = get_object_or_404(Hostel, id=hostel_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_floor':
            f_num = request.POST.get('floor_number', '').strip()
            total_rooms = request.POST.get('total_rooms', '0').strip()
            if f_num.isdigit():
                if Floor.objects.filter(hostel=hostel, floor_number=f_num).exists():
                    messages.error(request, f"Floor {f_num} already exists in {hostel.name}.")
                else:
                    f = Floor.objects.create(hostel=hostel, floor_number=int(f_num))
                    messages.success(request, f"Floor {f.floor_number} added to {hostel.name}.")
                    # Create rooms if total_rooms provided
                    if total_rooms.isdigit() and int(total_rooms) > 0:
                        tr = int(total_rooms)
                        for i in range(1, tr + 1):
                            r_name = f"{f_num}{i:02d}"
                            Room.objects.get_or_create(floor=f, room_number=r_name)
            else:
                messages.error(request, "Floor number must be an integer.")
            return redirect('admin_floor_dashboard', hostel_id=hostel.id)
            
        elif action == 'toggle_status':
            fid = request.POST.get('floor_id')
            f = get_object_or_404(Floor, id=fid, hostel=hostel)
            f.is_active = not f.is_active
            f.save()
            messages.success(request, f"Status for Floor {f.floor_number} toggled.")
            return redirect('admin_floor_dashboard', hostel_id=hostel.id)

    floors = hostel.floors.all().order_by('floor_number')
    return render(request, 'master_admin/floor_dashboard.html', {'profile': profile, 'hostel': hostel, 'floors': floors})

@login_required
def admin_room_dashboard(request, floor_id):
    profile = get_admin_profile(request)
    if not profile: return redirect('landing_page')

    floor = get_object_or_404(Floor, id=floor_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_room':
            r_name = request.POST.get('room_number', '').strip()
            if r_name:
                if Room.objects.filter(floor=floor, room_number=r_name).exists():
                    messages.error(request, f"Room '{r_name}' already exists on this floor.")
                else:
                    Room.objects.create(floor=floor, room_number=r_name)
                    messages.success(request, f"Room '{r_name}' created successfully.")
            else:
                messages.error(request, "Room number cannot be empty.")
            return redirect('admin_room_dashboard', floor_id=floor.id)
            
        elif action == 'toggle_status':
            rid = request.POST.get('room_id')
            r = get_object_or_404(Room, id=rid, floor=floor)
            r.is_active = not r.is_active
            r.save()
            messages.success(request, f"Status for Room {r.room_number} toggled.")
            return redirect('admin_room_dashboard', floor_id=floor.id)

    rooms = floor.rooms.all().order_by('room_number')
    return render(request, 'master_admin/room_dashboard.html', {'profile': profile, 'floor': floor, 'rooms': rooms})
