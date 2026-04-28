from django import forms
from .models import User
import re

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class SignupForm(forms.ModelForm):
    # 1. Define the restricted choices (exclude 'admin')
    SIGNUP_ROLES = (
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),
    )

    # 2. Override the role field with the restricted choices
    role = forms.ChoiceField(choices=SIGNUP_ROLES)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'role', 'password']

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if len(password) < 8 or len(password) >= 10:
            raise forms.ValidationError("Password must be 8 or 9 characters long.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[^A-Za-z0-9]', password):
            raise forms.ValidationError("Password must contain at least one special symbol.")
        return password
