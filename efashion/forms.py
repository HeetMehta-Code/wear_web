from django import forms
from .models import Vendor, Customer

class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['shopname', 'vendor_logo']
        widgets = {
            'shopname': forms.TextInput(attrs={
                'placeholder': 'ENTER YOUR SHOP NAME',
            }),
            # FileInput removes the "Currently: URL" and the checkbox
            'vendor_logo': forms.FileInput(attrs={
                'class': 'file-upload-input',
            }),
        }

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['address', 'profile_photo']
        widgets = {
            'address': forms.TextInput(attrs={
                'placeholder': 'ENTER YOUR DELIVERY ADDRESS',
            }),
            # FileInput removes the "Currently: URL" and the checkbox
            'profile_photo': forms.FileInput(attrs={
                'class': 'file-upload-input',
            }),
        }