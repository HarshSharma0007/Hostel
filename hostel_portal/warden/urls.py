from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.warden_dashboard, name='warden_dashboard'),
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('confirm-csv/', views.confirm_csv_upload, name='confirm_csv_upload'),
    path('send-invitations/', views.send_invitations, name='send_invitations'),
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('logout/', views.warden_logout_view, name='warden_logout'),
    path('email-center/', views.email_center, name='email_center'), 
]
