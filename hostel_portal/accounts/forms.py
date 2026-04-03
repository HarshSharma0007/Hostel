from django import forms
from .models import StudentProfile
from django.forms import ValidationError
import re

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'mobile', 'parent_mobile', 'alt_parent_mobile',
            'address', 'city', 'pin_code', 'state',
            'room_number', 'floor_number'
        ]
        widgets = {
            'mobile': forms.TextInput(attrs={'placeholder': '10-digit mobile number'}),
            'parent_mobile': forms.TextInput(attrs={'placeholder': '10-digit parent mobile number'}),
            'alt_parent_mobile': forms.TextInput(attrs={'placeholder': 'Alternate parent mobile number'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'city': forms.TextInput(),
            'pin_code': forms.TextInput(),
            'state': forms.TextInput(),
            'room_number': forms.TextInput(attrs={'placeholder': 'e.g. 101'}),
            'floor_number': forms.TextInput(attrs={'placeholder': 'e.g. 1st'}),
        }

    def _validate_mobile(self, number, field_name):
        if not number or not number.isdigit() or len(number) != 10:
            raise forms.ValidationError("Must be exactly 10 digits.")

        # Must start with 6–9
        if not number.startswith(('6', '7', '8', '9')):
            raise forms.ValidationError("Must start with 6, 7, 8, or 9.")

        # Reject generic or fake numbers
        fake_patterns = [
            '0000000000', '1234567890', '9876543210', '9999999999',
            '1111111111', '2222222222', '3333333333', '4444444444',
            '5555555555', '6666666666', '7777777777', '8888888888'
        ]
        if number in fake_patterns:
            raise forms.ValidationError("Enter a valid, non-generic mobile number.")

        return number

    def clean_mobile(self):
        return self._validate_mobile(self.cleaned_data.get('mobile'), 'mobile')

    def clean_parent_mobile(self):
        return self._validate_mobile(self.cleaned_data.get('parent_mobile'), 'parent_mobile')

    def clean_alt_parent_mobile(self):
        alt = self.cleaned_data.get('alt_parent_mobile')
        if alt:
            return self._validate_mobile(alt, 'alt_parent_mobile')
        return alt

    

    def clean(self):
        cleaned_data = super().clean()
        mobile = cleaned_data.get('mobile')
        parent = cleaned_data.get('parent_mobile')
        alt = cleaned_data.get('alt_parent_mobile')

        numbers = [n for n in [mobile, parent, alt] if n]
        if len(set(numbers)) < len(numbers):
            raise ValidationError("All mobile numbers must be different from one another.")

        return cleaned_data

