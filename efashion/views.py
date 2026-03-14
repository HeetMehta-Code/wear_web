from django.shortcuts import render, redirect
from .forms import VendorCompleteForm, CustomerCompleteForm

def complete_profile_view(request):
    user = request.user
    if user.role == 'vendor':
        profile = user.vendor_profile
        form_class = VendorCompleteForm
        next_url = 'vendor_dashboard'
    else:
        profile = user.customer_profile
        form_class = CustomerCompleteForm
        next_url = 'customer_dashboard'

    if request.method == 'POST':
        # request.FILES is required for Cloudinary
        form = form_class(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(next_url)
    else:
        form = form_class(instance=profile)
        
    return render(request, 'Customers/ccp.html', {'form': form})