from django import forms
from django.core.validators import RegexValidator
from .models import StudentProfile
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            # 'name', 'enrollment_number',  # ✅ Add these
            'mobile', 'parent_mobile', 'alt_parent_mobile',
            'address', 'city', 'pin_code', 'state'
        ]
        widgets = {
            # 'name': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            # 'enrollment_number': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'placeholder': '10-digit mobile number'}),
            'parent_mobile': forms.TextInput(attrs={'placeholder': '10-digit parent mobile number'}),
            'alt_parent_mobile': forms.TextInput(attrs={'placeholder': 'Alternate parent mobile number'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Permanent address'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'pin_code': forms.TextInput(attrs={'placeholder': 'PIN code'}),
            'state': forms.TextInput(attrs={'placeholder': 'State'}),
        }

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not mobile or not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return mobile

    def clean_parent_mobile(self):
        mobile = self.cleaned_data.get('parent_mobile')
        if not mobile or not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError("Enter a valid 10-digit parent mobile number.")
        return mobile

    def clean_alt_parent_mobile(self):
        mobile = self.cleaned_data.get('alt_parent_mobile')
        if mobile and (not mobile.isdigit() or len(mobile) != 10):
            raise forms.ValidationError("Enter a valid 10-digit alternate parent mobile number.")
        return mobile
