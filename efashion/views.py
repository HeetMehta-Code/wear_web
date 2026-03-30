from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum
from.models import Vendor, Customer, Product, Order, Color, Size, ProductVariant
# Importing forms and models from your apps
from .forms import SignupForm, LoginForm
from efashion.models import Vendor, Customer, Product, Order, Color, Size, ProductVariant
from efashion.forms import VendorProfileForm, CustomerProfileForm
from django.db.models import Q, Sum
# ═══════════════════════════════════════════════════════════════════
# 1. AUTHENTICATION (Keep as is)
# ═══════════════════════════════════════════════════════════════════

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
                    vendor, _ = Vendor.objects.get_or_create(user=user)
                    if not vendor.shopname:
                        return redirect("complete_profile")
                    return redirect("vendor_dashboard")
                elif user.role == "customer":
                    customer, _ = Customer.objects.get_or_create(user=user)
                    if not customer.address:
                        return redirect("complete_profile")
                    return redirect("customer_dashboard")
            else:
                form.add_error(None, "Invalid email or password")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect('login')

# ═══════════════════════════════════════════════════════════════════
# 2. PROFILE ROUTING (Handles ccp.html for Customers)
# ═══════════════════════════════════════════════════════════════════

@login_required
def complete_profile(request):
    """ This view handles the ACTUAL form-saving for profiles (ccp.html/cvp.html) """
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

# ═══════════════════════════════════════════════════════════════════
# 3. CUSTOMER VIEWS (customer_profile.html)
# ═══════════════════════════════════════════════════════════════════

@login_required
def customer_dashboard(request):
    customer = get_object_or_404(Customer, user=request.user)
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True).order_by('-created_at')[:12]
    return render(request, "Customers/customers.html", {
        "customer": customer,
        "new_arrivals": new_arrivals,
    })

@login_required
def customer_profile(request):
    """ Displays stats and orders. Button here links to complete_profile for ccp.html """
    customer = get_object_or_404(Customer, user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-orderDate')
    return render(request, 'Customers/customer_profile.html', {
        'customer': customer,
        'orders': orders,
        'order_count': orders.count(),
    })
def search_view(request):
    query = request.GET.get('q', '')
    # icontains makes it case-insensitive
    results = Product.objects.filter(Q(name__icontains=query) | Q(category__icontains=query))
    return render(request, 'search_results.html', {'products': results, 'query': query})

def brand_product_view(request, brand_name):
    products = Product.objects.filter(brand_name__iexact=brand_name, is_active=True)
    
    return render(request, "Customers/brand_all.html", {
        "products": products,
        "brand_name": brand_name,  # Changed from category_name to brand_name
    })

def feature_collection_view(request, feature_type):
    # Logic for Trending, Best Sellers, etc.
    if feature_type == 'trending':
        products = Product.objects.filter(is_trending=True) # Assumes boolean fields in model
    elif feature_type == 'limited':
        products = Product.objects.filter(stock__lt=5)
    else:
        products = Product.objects.all() # Fallback
        
    return render(request, 'feature_collection.html', {'products': products, 'title': feature_type.title()})

def about_us(request):
    return render(request, 'about.html')

def contact_us(request):
    return render(request, 'contact.html')

from django.shortcuts import render
from .models import Product

# views.py
def category_view(request, cat_slug, sub_slug=None):
    # 1. Start by filtering the main category (e.g., 'mens')
    products = Product.objects.filter(category=cat_slug, is_active=True)
    
    # 2. Define the title map for the sidebar/heading
    category_titles = {
        'mens': "Men's Wear", 'womens': "Women's Wear", 'kids': "Kid's Wear",
        'bags': "Bags", 'purses': "Purses", 'belts': "Belts",
        'sunglasses': "Sun Glasses", 'makeup': "Makeup", 'footwear': "Footwear",
    }
    
    display_name = category_titles.get(cat_slug, cat_slug.title())

    # 3. If a circle button was clicked (e.g., 'jacket'), filter further
    if sub_slug:
        # This looks for the 'sub_category' field in your Product model
        products = products.filter(sub_category__iexact=sub_slug)
        display_name = f"{sub_slug.title()} ({display_name})"

    return render(request, "Customers/shop_all.html", {
        "products": products,
        "category_name": display_name,
    })
# ═══════════════════════════════════════════════════════════════════
# 4. VENDOR VIEWS (profile.html & vendors.html)
# ═══════════════════════════════════════════════════════════════════

@login_required
def vendor_dashboard(request):
    # 1. Get the specific vendor profile
    vendor = get_object_or_404(Vendor, user=request.user)
    
    # 2. Start with all products belonging to this vendor
    products = Product.objects.filter(vendor=vendor).order_by('-created_at')
    
    # 3. Handle Search Query (Non-Case Sensitive)
    query = request.GET.get('q', '').strip()
    if query:
        # icontains = Case-Insensitive search
        products = products.filter(
            Q(name__icontains=query) | 
            Q(category__icontains=query) | 
            Q(sub_category__icontains=query) |
            Q(brand_name__icontains=query)
        )
    
    # 4. Calculate Global Stats (Based on filtered results)
    stats = products.aggregate(
        total_views=Sum('view_count'),
        total_stock=Sum('stock')
    )
    
    total_views = stats['total_views'] or 0
    total_stock = stats['total_stock'] or 0

    # 5. Pie Chart Data (Top 5 most viewed from the current list)
    top_products = products.order_by('-view_count')[:5]
    labels = [p.name for p in top_products]
    chart_data = [p.view_count for p in top_products]

    # 6. Render
    return render(request, "Vendors/vendors.html", {
        "vendor": vendor,
        "products": products, # This will be the filtered list
        "labels": labels,
        "chart_data": chart_data,
        "total_views": total_views,
        "total_stock": total_stock,
        "query": query, # Passing query back helps show "Results for..." in UI
    })

@login_required
def vendor_profile_view(request):
    # 1. Get the vendor object
    vendor = get_object_or_404(Vendor, user=request.user)

    if request.method == "POST":
        # 2. Update logic
        vendor.shopname = request.POST.get('shopname')
        vendor.shop_address = request.POST.get('shop_address')
        
        if request.FILES.get('vendor_logo'):
            vendor.vendor_logo = request.FILES.get('vendor_logo')
            
        vendor.save()
        messages.success(request, "Shop details updated!")
        return redirect('vendor_dashboard')

    # 3. Render the SPECIFIC Vendor profile template
    return render(request, "Vendors/profile.html", {"vendor": vendor})

@login_required
def vendor_edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor__user=request.user)
    
    if request.method == "POST":
        product.name = request.POST.get('name')
        product.brand_name = request.POST.get('brand')
        product.category = request.POST.get('category')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.description = request.POST.get('description')
        
        if request.FILES.get('product_image'):
            product.product_image = request.FILES.get('product_image')
            
        product.save()
        messages.success(request, f'"{product.name}" updated successfully!')
        return redirect('vendor_dashboard')

    return render(request, "Vendors/edit_product.html", {"product": product})

# ─── DELETE PRODUCT ───
@login_required
def vendor_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor__user=request.user)
    product.delete()
    messages.warning(request, "Product has been deleted.")
    return redirect('vendor_dashboard')
# ═══════════════════════════════════════════════════════════════════
# 5. PRODUCT & API HELPERS
# ═══════════════════════════════════════════════════════════════════

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Ensure your model has an increment_views() method
    if hasattr(product, 'increment_views'):
        product.increment_views() 
    return render(request, "Customers/product_detail.html", {"product": product})

@login_required
@require_POST
def vendor_toggle_product(request, product_id):
    vendor = get_object_or_404(Vendor, user=request.user)
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    product.is_active = not product.is_active
    product.save()
    return JsonResponse({'status': 'ok', 'is_active': product.is_active})

def all_new_arrivals(request):
    products = Product.objects.filter(is_active=True).order_by('-created_at')[:10]
    data = [{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'image_url': p.product_image.url if p.product_image else '/static/images/default.jpg',
        'category': p.get_category_display(),
    } for p in products]
    return JsonResponse({'products': data})

# ═══════════════════════════════════════════════════════════════════
# 5. VENDOR UPLOAD PRODUCT (ADD THIS BACK)
# ═══════════════════════════════════════════════════════════════════

@login_required
def vendor_upload_product(request):
    vendor = get_object_or_404(Vendor, user=request.user)

    if request.method == "POST":
        # 1. Collect Form Data
        name = request.POST.get('name')
        category = request.POST.get('category')
        sub_category = request.POST.get('sub_category')
        price = request.POST.get('price')
        description = request.POST.get('description')
        brand = request.POST.get('brand', 'Generic')

        # 2. Collect Variant Lists
        colors = request.POST.getlist('variant_color[]')
        sizes = request.POST.getlist('variant_size[]')
        qtys = request.POST.getlist('variant_qty[]')
        variant_photos = request.FILES.getlist('variant_image[]')

        # 3. Calculate Total Stock and Identify Main Image
        total_stock = sum(int(q) for q in qtys if q)
        # Use the very first image uploaded in the variants as the primary photo
        main_product_photo = variant_photos[0] if variant_photos else None

        # 4. Create Parent Product
        product = Product.objects.create(
            vendor=vendor,
            name=name,
            brand_name=brand,
            category=category,
            sub_category=sub_category,
            price=price,
            stock=total_stock,
            description=description,
            product_image=main_product_photo, # Saved to Cloudinary automatically
            is_active=True
        )

        # 5. Create Variants
        for i in range(len(colors)):
            if colors[i] or sizes[i] or (i < len(qtys) and qtys[i]):
                # Handle Foreign Keys for Color/Size
                c_obj, _ = Color.objects.get_or_create(name=colors[i].strip().title()) if colors[i] else (None, False)
                s_obj, _ = Size.objects.get_or_create(name=sizes[i].strip().upper()) if sizes[i] else (None, False)
                
                # Get specific image for this row
                v_photo = variant_photos[i] if i < len(variant_photos) else None

                ProductVariant.objects.create(
                    product=product,
                    color=c_obj,
                    size=s_obj,
                    variant_stock=int(qtys[i]) if (i < len(qtys) and qtys[i]) else 0,
                    image=v_photo # Saved to Cloudinary folder 'Products/Variants/'
                )

        messages.success(request, f'Product "{name}" published with variants!')
        return redirect('vendor_dashboard')

    return render(request, "Vendors/upload_product.html")
# -----------------------------
# CATEGORY VIEWS (Now properly defined)
# -----------------------------

def mens_wear(request):
    products = Product.objects.filter(category='mens', is_active=True)
    return render(request, "Customers/mens_wear.html", {"products": products})

def womens_wear(request):
    products = Product.objects.filter(category='womens', is_active=True)
    return render(request, "Customers/womens_wear.html", {"products": products})

def kids_wear(request):
    products = Product.objects.filter(category='kids', is_active=True)
    return render(request, "Customers/kids_wear.html", {"products": products})

# -----------------------------
# PRODUCT DETAIL (Important for clicking items)
# -----------------------------

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # If your model has the increment_views method for the dashboard chart:
    if hasattr(product, 'increment_views'):
        product.increment_views()
        
    return render(request, "Customers/product_detail.html", {"product": product})