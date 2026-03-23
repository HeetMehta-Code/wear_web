from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from .forms import SignupForm, LoginForm

from efashion.models import Vendor, Customer, Product, Order
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
            email    = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user     = authenticate(request, email=email, password=password)
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
    customer     = Customer.objects.get(user=request.user)
    new_arrivals = (
        Product.objects
        .filter(is_active=True, is_new_arrival=True)
        .select_related('vendor')
        .order_by('-created_at')[:12]
    )
    return render(request, "Customers/customers.html", {
        "customer":     customer,
        "new_arrivals": new_arrivals,
    })


# -----------------------------
# CUSTOMER PROFILE PAGE
# -----------------------------
@login_required
def customer_profile(request):
    customer = Customer.objects.get(user=request.user)
    orders   = Order.objects.filter(customer=customer).order_by('-orderDate')
    return render(request, 'Customers/customer_profile.html', {
        'customer':    customer,
        'orders':      orders,
        'order_count': orders.count(),
    })


# -----------------------------
# LOGOUT
# -----------------------------
def logout_view(request):
    logout(request)
    return redirect("login")


# -----------------------------
# NEW ARRIVALS API
# -----------------------------
def all_new_arrivals(request):
    products = (
        Product.objects
        .filter(is_active=True, is_new_arrival=True)
        .select_related('vendor')
        .order_by('-created_at')
    )
    data = []
    for p in products:
        data.append({
            'id':             p.id,
            'name':           p.name,
            'brand':          p.vendor.shopname or '',
            'category':       p.get_category_display(),
            'price':          p.price,
            'original_price': p.original_price,
            'discount':       p.discount_percent,
            'image':          p.product_image.url if p.product_image else '',
        })
    return JsonResponse({'products': data})


# -----------------------------
# VENDOR UPLOAD PRODUCT
# -----------------------------
@login_required
def vendor_upload_product(request):
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        return redirect('complete_profile')

    if request.method == 'POST':
        name           = request.POST.get('name', '').strip()
        category       = request.POST.get('category', 'other')
        price          = request.POST.get('price')
        original_price = request.POST.get('original_price') or None
        stock          = request.POST.get('stock', 0)
        image          = request.FILES.get('product_image')

        if not all([name, price, stock, image]):
            messages.error(request, "Name, price, stock and image are required.")
        else:
            Product.objects.create(
                vendor=vendor,
                name=name,
                category=category,
                price=price,
                original_price=original_price,
                stock=stock,
                product_image=image,
                is_active=True,
                is_new_arrival=True,
            )
            messages.success(request, f'"{name}" is now live on the homepage!')
            return redirect('vendor_dashboard')

    return render(request, 'Vendors/vendor_upload.html', {
        'category_choices': Product.CATEGORY_CHOICES,
    })


# -----------------------------
# VENDOR TOGGLE PRODUCT
# -----------------------------
@login_required
@require_POST
def vendor_toggle_product(request, product_id):
    try:
        vendor  = Vendor.objects.get(user=request.user)
        product = Product.objects.get(id=product_id, vendor=vendor)
        product.is_active = not product.is_active
        product.save()
        return JsonResponse({'status': 'ok', 'is_active': product.is_active})
    except (Vendor.DoesNotExist, Product.DoesNotExist):
        return JsonResponse({'status': 'error'}, status=403)