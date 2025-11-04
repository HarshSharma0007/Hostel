from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.warden_dashboard, name='warden_dashboard'),
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('complaints/', views.complaint_list, name='complaint_list'),
]
