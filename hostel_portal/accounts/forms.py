from django import forms
from .models import StudentProfile
from django.forms import ValidationError
import re

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['mobile']
        widgets = {
            'mobile': forms.TextInput(attrs={'placeholder': '10-digit mobile number'}),
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

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

