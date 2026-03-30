from django import forms
from django.contrib.auth import get_user_model
from .models import Vendor, Customer

User = get_user_model()

# --- AUTH FORMS (Needed for signup_view and login_view) ---

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Create a password'
    }))
    
    class Meta:
        model = User
        fields = ['email', 'password', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))


# --- PROFILE FORMS (Your existing code) ---

class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['shopname', 'vendor_logo']
        widgets = {
            'shopname': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor_logo': forms.FileInput(attrs={'class': 'file-upload-input'}),
        }

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['address', 'profile_photo']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'file-upload-input'}),
        }