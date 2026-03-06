from django.shortcuts import render, redirect
from .forms import SignupForm, LoginForm
from django.contrib.auth import authenticate, login, logout
from efashion.decorators import allowed_users

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                
                # --- DYNAMIC REDIRECT LOGIC ---
                if user.role == 'vendor':
                    return redirect('vendor_dashboard')
                elif user.role == 'customer':
                    return redirect('customer_dashboard')
                elif user.is_superuser:
                    return redirect('/admin/') # Default Django admin
                else:
                    return redirect('login') # Fallback
                # ------------------------------
            else:
                form.add_error(None, "Invalid email or password")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# Add a logout view to handle the button click
def logout_view(request):
    logout(request)
    return redirect('login')

@allowed_users(allowed_roles=['vendor'])
def vendor_dashboard(request):
    return render(request, 'Vendors/vendors.html')

@allowed_users(allowed_roles=['customer'])
def customer_dashboard(request):
    return render(request, 'Customers/customers.html')