from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='faculty_dashboard'),
    path('complaint/<int:complaint_id>/', views.complaint_detail_view, name='faculty_complaint_detail'),
    path('search-students/', views.student_search_view, name='faculty_student_search'),
]
