from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm, LoginForm

from efashion.models import Vendor, Customer
from efashion.forms import VendorProfileForm, CustomerProfileForm


# -----------------------------
# SIGNUP
# -----------------------------
def signup_view(request):

    if request.method == "POST":

        form = SignupForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            if user.role == "vendor":
                Vendor.objects.create(user=user)

            elif user.role == "customer":
                Customer.objects.create(user=user)

            return redirect("login")

    else:
        form = SignupForm()

    return render(request, "signup.html", {"form": form})


# -----------------------------
# LOGIN
# -----------------------------
def login_view(request):

    if request.method == "POST":

        form = LoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(request, email=email, password=password)

            if user is not None:

                login(request, user)

                if user.role == "vendor":

                    vendor = Vendor.objects.get(user=user)

                    if not vendor.shopname or not vendor.vendor_logo:
                        return redirect("complete_profile")

                    return redirect("vendor_dashboard")

                elif user.role == "customer":

                    customer = Customer.objects.get(user=user)

                    if not customer.address or not customer.profile_photo:
                        return redirect("complete_profile")

                    return redirect("customer_dashboard")

            else:
                form.add_error(None, "Invalid email or password")

    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


# -----------------------------
# COMPLETE PROFILE
# -----------------------------
def complete_profile(request):

    user = request.user

    if user.role == "vendor":

        vendor = Vendor.objects.get(user=user)

        if request.method == "POST":

            form = VendorProfileForm(request.POST, request.FILES, instance=vendor)

            if form.is_valid():
                form.save()
                return redirect("vendor_dashboard")

        else:
            form = VendorProfileForm(instance=vendor)

        return render(request, "Vendors/cvp.html", {"form": form})


    elif user.role == "customer":

        customer = Customer.objects.get(user=user)

        if request.method == "POST":

            form = CustomerProfileForm(request.POST, request.FILES, instance=customer)

            if form.is_valid():
                form.save()
                return redirect("customer_dashboard")

        else:
            form = CustomerProfileForm(instance=customer)

        return render(request, "Customers/ccp.html", {"form": form})


# -----------------------------
# DASHBOARDS
# -----------------------------
def vendor_dashboard(request):

    vendor = Vendor.objects.get(user=request.user)

    return render(request, "Vendors/vendors.html", {"vendor": vendor})


def customer_dashboard(request):

    customer = Customer.objects.get(user=request.user)

    return render(request, "Customers/customers.html", {"customer": customer})


# -----------------------------
# LOGOUT
# -----------------------------
def logout_view(request):

    logout(request)

    return redirect("login")