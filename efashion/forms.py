from django import forms
from django.contrib.auth import get_user_model
from .models import Vendor, Customer
import re

User = get_user_model()

# --- AUTH FORMS (Needed for signup_view and login_view) ---

class SignupForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=(
            ('vendor', 'Vendor'),
            ('customer', 'Customer'),
        ),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Create a password'
    }))
    
    class Meta:
        model = User
        fields = ['email', 'password', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if len(password) < 8 or len(password) >= 10:
            raise forms.ValidationError("Password must be 8 or 9 characters long.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[^A-Za-z0-9]', password):
            raise forms.ValidationError("Password must contain at least one special symbol.")
        return password

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
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
        label='New Password'
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
        label='Confirm Password'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address', 'profile_photo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter full address'}),
            'profile_photo': forms.FileInput(attrs={'class': 'file-upload-input'}),
        }

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if phone and not re.fullmatch(r'\d{10}', phone):
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password', '')
        confirm_password = cleaned_data.get('confirm_password', '')

        if new_password:
            if len(new_password) < 8 or len(new_password) >= 10:
                self.add_error('new_password', "Password must be 8 or 9 characters long.")
            if not re.search(r'[A-Z]', new_password):
                self.add_error('new_password', "Password must contain at least one uppercase letter.")
            if not re.search(r'[^A-Za-z0-9]', new_password):
                self.add_error('new_password', "Password must contain at least one special symbol.")
            if not confirm_password:
                self.add_error('confirm_password', "Confirm your new password.")
            elif new_password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
        elif confirm_password:
            self.add_error('new_password', "Enter a new password first.")

        return cleaned_data
