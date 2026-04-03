from django.db import models
from accounts.models import StudentProfile

class ComplaintCategory(models.Model):
    """
    Dynamically defined by the Warden (e.g., Water, Sanitation, Electricity).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CategoryField(models.Model):
    """
    Specific dynamic inputs attached to a category.
    """
    FIELD_TYPES = (
        ('text', 'Short Text'),
        ('textarea', 'Long Text (Paragraph)'),
        ('dropdown', 'Dropdown Selection'),
        ('number', 'Positive Number'),
        ('image', 'Image Upload'),
        ('checkbox', 'Checkbox'),
    )

    category = models.ForeignKey(ComplaintCategory, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=200) # The question asked (e.g., "Where is the leak?")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    is_required = models.BooleanField(default=True)
    options = models.TextField(blank=True, null=True, help_text="[Legacy] Comma-separated options for dropdowns")
    parent_option = models.ForeignKey('FieldOption', on_delete=models.SET_NULL, blank=True, null=True, related_name='child_fields')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.category.name} - {self.label}"

class FieldOption(models.Model):
    """
    Individual choice for a 'dropdown' field.
    Can have multiple child_fields that appear when selected.
    """
    field = models.ForeignKey(CategoryField, on_delete=models.CASCADE, related_name='field_options')
    text = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.field.label} -> {self.text}"

class Complaint(models.Model):
    """
    The actual ticket submitted by the student.
    """
    STATUS_CHOICES = (
        ('NotResolved', 'Pending'),
        ('InProgress', 'In Progress'),
        ('Resolved', 'Resolved'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='complaints')
    category = models.ForeignKey(ComplaintCategory, on_delete=models.CASCADE, related_name='complaints')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NotResolved')
    ticket_number = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    
    # Generic short title or description if needed, or we just rely on the dynamic fields
    custom_title = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Auto-generate: TKT-0001, TKT-0002, etc.
            last = Complaint.objects.order_by('-id').first()
            next_num = (last.id + 1) if last else 1
            self.ticket_number = f"TKT-{next_num:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} by {self.student.enrollment_number} ({self.status})"

class ComplaintFieldValue(models.Model):
    """
    The student's dynamic answers to the CategoryField questions.
    """
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='field_values')
    field = models.ForeignKey(CategoryField, on_delete=models.CASCADE)
    
    # Text-based answers
    text_value = models.TextField(blank=True, null=True)
    
    # For image uploads
    image_value = models.ImageField(upload_to='complaint_images/', blank=True, null=True)

    def __str__(self):
        return f"Answer for {self.field.label} on Complaint #{self.complaint.id}"
