from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='admin_root'),
    path('dashboard/', views.dashboard_view, name='admin_dashboard'),
    path('search/', views.search_users_view, name='admin_search_users'),
    path('manage-staff/', views.manage_staff_view, name='admin_manage_staff'),
    path('complaints/', views.complaint_manager_view, name='admin_complaint_manager'),
    path('hostels/', views.admin_hostel_dashboard, name='admin_hostel_dashboard'),
    path('hostels/<int:hostel_id>/floors/', views.admin_floor_dashboard, name='admin_floor_dashboard'),
    path('floors/<int:floor_id>/rooms/', views.admin_room_dashboard, name='admin_room_dashboard'),
    
    # Edit profile overrides
    path('edit-student/<str:student_id>/', views.edit_student_view, name='admin_edit_student'),
    path('edit-faculty/<int:faculty_id>/', views.edit_faculty_view, name='admin_edit_faculty'),
    path('edit-warden/<str:warden_key>/', views.edit_warden_view, name='admin_edit_warden'),
    
    # Override complaint status
    path('edit-complaint/<int:complaint_id>/', views.edit_complaint_view, name='admin_edit_complaint'),
]
