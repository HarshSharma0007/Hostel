from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    
    path('categories/<int:pk>/builder/', views.CategoryBuilderView.as_view(), name='category_builder'),
    
    path('categories/<int:category_id>/fields/new/', views.FieldCreateView.as_view(), name='field_create'),
    path('fields/<int:pk>/edit/', views.FieldUpdateView.as_view(), name='field_edit'),
    path('fields/<int:pk>/delete/', views.FieldDeleteView.as_view(), name='field_delete'),
    path('api/fields/reorder/', views.api_reorder_fields, name='api_reorder_fields'),
    path('api/fields/<int:field_id>/options/add/', views.api_add_field_option, name='api_add_field_option'),
    path('api/options/<int:option_id>/delete/', views.api_delete_field_option, name='api_delete_field_option'),

    # Student URLs
    path('student/', views.student_complaint_list, name='student_complaint_list'),
    path('student/submit/', views.student_submit_complaint, name='student_submit_complaint'),
    path('api/categories/<int:category_id>/fields/', views.api_get_category_fields, name='api_get_category_fields'),
]
