from django import forms
from .models import User

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