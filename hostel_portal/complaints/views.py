from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse

from .models import ComplaintCategory, CategoryField, FieldOption, Complaint, ComplaintFieldValue

# ==========================================
# WARDEN VIEWS
# ==========================================

class WardenMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'wardenprofile')

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized as a warden.")
        return redirect('logout')

class CategoryListView(WardenMixin, ListView):
    model = ComplaintCategory
    template_name = 'complaints/category_list.html'
    context_object_name = 'categories'

class CategoryCreateView(WardenMixin, CreateView):
    model = ComplaintCategory
    fields = ['name', 'description', 'is_active']
    template_name = 'complaints/category_form.html'
    
    def get_success_url(self):
        return reverse_lazy('category_builder', kwargs={'pk': self.object.pk})

class CategoryUpdateView(WardenMixin, UpdateView):
    model = ComplaintCategory
    fields = ['name', 'description', 'is_active']
    template_name = 'complaints/category_form.html'
    success_url = reverse_lazy('category_list')


class CategoryBuilderView(WardenMixin, DetailView):
    """
    Shows the visual builder for a specific category where wardens can add/remove fields.
    """
    model = ComplaintCategory
    template_name = 'complaints/category_builder.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only show top-level fields in the root list; children will be nested
        context['root_fields'] = self.object.fields.filter(parent_option__isnull=True).order_by('order')
        return context

class FieldCreateView(WardenMixin, CreateView):
    model = CategoryField
    fields = ['label', 'field_type', 'is_required', 'order']
    template_name = 'complaints/field_form.html'

    def form_valid(self, form):
        category = get_object_or_404(ComplaintCategory, pk=self.kwargs['category_id'])
        form.instance.category = category
        
        # If parent_option_id is provided, link it
        parent_option_id = self.request.GET.get('parent_option')
        if parent_option_id:
            form.instance.parent_option = get_object_or_404(FieldOption, pk=parent_option_id)
            
        if form.instance.order == 0:
            # Count fields within the same parent/context for automatic ordering
            count = CategoryField.objects.filter(
                category=category, 
                parent_option=form.instance.parent_option
            ).count()
            form.instance.order = count
            
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('category_builder', kwargs={'pk': self.kwargs['category_id']})

class FieldUpdateView(WardenMixin, UpdateView):
    model = CategoryField
    fields = ['label', 'field_type', 'is_required', 'order']
    template_name = 'complaints/field_form.html'

    def get_success_url(self):
        return reverse_lazy('category_builder', kwargs={'pk': self.object.category.id})

class FieldDeleteView(WardenMixin, DeleteView):
    model = CategoryField
    
    def get_success_url(self):
        return reverse_lazy('category_builder', kwargs={'pk': self.object.category.id})

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@login_required
def api_reorder_fields(request):
    """
    AJAX endpoint to save the new order of fields for a category.
    Now supports nested reordering by moving fields between parent options.
    """
    if not hasattr(request.user, 'wardenprofile'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # data format: { "parent_id": null or opt_id, "order": [id, id, id] }
            order_data = data.get('order', [])
            parent_option_id = data.get('parent_id')
            
            parent_opt = None
            if parent_option_id:
                parent_opt = get_object_or_404(FieldOption, pk=parent_option_id)
            
            for index, field_id in enumerate(order_data):
                CategoryField.objects.filter(id=field_id).update(
                    order=index,
                    parent_option=parent_opt
                )
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@csrf_exempt
@login_required
def api_add_field_option(request, field_id):
    if not hasattr(request.user, 'wardenprofile'):
        return JsonResponse({'status': 'error'}, status=403)
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        if text:
            field = get_object_or_404(CategoryField, id=field_id)
            option = FieldOption.objects.create(field=field, text=text)
            return JsonResponse({'status': 'success', 'id': option.id, 'text': option.text})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@login_required
def api_delete_field_option(request, option_id):
    if not hasattr(request.user, 'wardenprofile'):
        return JsonResponse({'status': 'error'}, status=403)
    if request.method == 'POST':
        option = get_object_or_404(FieldOption, id=option_id)
        option.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# ==========================================
# STUDENT VIEWS
# ==========================================

@login_required
def api_get_category_fields(request, category_id):
    """
    Returns the dynamic fields required for a given category as JSON.
    Supports hierarchical structure for conditional branching.
    """
    if hasattr(request, 'user') and hasattr(request.user, 'wardenprofile'):
        cat = get_object_or_404(ComplaintCategory, id=category_id)
    else:
        cat = get_object_or_404(ComplaintCategory, id=category_id, is_active=True)
        
    fields = cat.fields.all().order_by('order')
    
    data = []
    for f in fields:
        field_data = {
            'id': f.id,
            'label': f.label,
            'field_type': f.field_type,
            'is_required': f.is_required,
            'parent_option': f.parent_option.id if f.parent_option else None,
            'options': []
        }
        
        # Get options for dropdown fields
        if f.field_type == 'dropdown':
            options = f.field_options.all()
            for opt in options:
                field_data['options'].append({
                    'id': opt.id,
                    'text': opt.text
                })
        
        data.append(field_data)
        
    return JsonResponse({'fields': data})

@login_required
def student_submit_complaint(request):
    email = request.user.email.lower()
    
    # 🛑 CRITICAL SECURITY: Wardens (@gmail.com) should NEVER access this
    if email.endswith('@gmail.com'):
        messages.error(request, "Warden accounts cannot submit student complaints.")
        return redirect('logout')

    if not email.endswith('@mitsgwl.ac.in'):
        return redirect('logout')

    if not hasattr(request.user, 'studentprofile'):
        messages.error(request, "No student profile found for your account.")
        return redirect('logout')

    profile = request.user.studentprofile
    # 🕵️ Security Check: If profile is incomplete, force edit
    if profile.name == 'Unknown' or not profile.mobile:
        messages.warning(request, "Please complete your profile details before submitting a complaint.")
        return redirect('profile_edit')

    if request.method == 'POST':
        category_id = request.POST.get('category')
        if not category_id:
            messages.error(request, "Please select a complaint category.")
            return redirect('student_submit_complaint')
            
        category = get_object_or_404(ComplaintCategory, id=category_id, is_active=True)
        
        # Determine a title automatically based on category
        title = f"{category.name} Issue"
        
        complaint = Complaint.objects.create(
            student=profile,
            category=category,
            custom_title=title
        )
        
        # Save dynamic fields
        for field in category.fields.all():
            val = request.POST.get(f'custom_field_{field.id}', '')
            img = request.FILES.get(f'custom_field_{field.id}')
            
            # Special case for checkbox (HTML sends 'on' if checked, nothing if unchecked)
            if field.field_type == 'checkbox':
                val = 'Yes' if val == 'on' else 'No'
            elif field.field_type == 'dropdown':
                # Convert the submitted option ID back to the corresponding text
                if val:
                    try:
                        from .models import FieldOption
                        option = FieldOption.objects.get(id=val)
                        val = option.text
                    except (FieldOption.DoesNotExist, ValueError):
                        pass

            ComplaintFieldValue.objects.create(
                complaint=complaint,
                field=field,
                text_value=val,
                image_value=img if field.field_type == 'image' else None
            )
        
        return redirect('student_complaint_list')
        
    categories = ComplaintCategory.objects.filter(is_active=True)
    return render(request, 'complaints/student_submit.html', {'categories': categories, 'profile': profile})

@login_required
def student_complaint_list(request):
    email = request.user.email.lower()
    
    # 🛑 CRITICAL SECURITY: Wardens (@gmail.com) should NEVER access this
    if email.endswith('@gmail.com'):
        messages.error(request, "Warden accounts cannot access student complaint lists.")
        return redirect('logout')

    if not email.endswith('@mitsgwl.ac.in'):
        return redirect('logout')

    if not hasattr(request.user, 'studentprofile'):
        return redirect('logout')
    
    profile = request.user.studentprofile
    # 🕵️ Security Check: If profile is incomplete, force edit
    if profile.name == 'Unknown' or not profile.mobile:
        return redirect('profile_edit')
        
    complaints = Complaint.objects.filter(student=profile).order_by('-created_at')
    return render(request, 'complaints/student_list.html', {'complaints': complaints, 'profile': profile})
