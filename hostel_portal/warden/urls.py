from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
urlpatterns = [
    path('dashboard/', views.warden_dashboard, name='warden_dashboard'),
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('logout/', LogoutView.as_view(), name='warden_logout'),
]
