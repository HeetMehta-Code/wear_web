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
from efashion.models import Vendor, Customer, Product, Order, Color, Size, ProductVariant, Payment
from efashion.forms import VendorProfileForm, CustomerProfileForm
from django.db.models import Q, Sum
import razorpay
import hmac
import hashlib
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
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
    query = request.GET.get('q', '').strip()
    results = Product.objects.none()
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(vendor__shopname__icontains=query)
        ).filter(is_active=True).select_related('vendor')
    return render(request, 'Customers/shop_all.html', {
        'products': results,
        'query': query,
        'category_name': f'Search: "{query}"' if query else 'All Products',
    })

@login_required
def my_orders(request):
    customer = get_object_or_404(Customer, user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-orderDate')
    return render(request, 'Customers/myorders.html', {
        'orders': orders,
    })

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
    return render(request, 'Customers/about.html')

def contact_us(request):
    return render(request, 'Customers/contact.html')

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    for product_id, item_data in cart.items():
        product = get_object_or_404(Product, id=product_id)
        total_item_price = product.price * item_data['quantity']
        total_price += total_item_price
        cart_items.append({
            'product': product,
            'quantity': item_data['quantity'],
            'total_item_price': total_item_price,
        })

    return render(request, 'Customers/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {'quantity': 1}
    
    request.session['cart'] = cart
    return redirect('view_cart')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
    request.session['cart'] = cart
    return redirect('view_cart')

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

    # 6. Accounting — orders linked to this vendor's products
    from efashion.models import Payment
    vendor_orders = Order.objects.filter(
        payment__paymentStatus='Completed'
    ).select_related('payment').prefetch_related('orderitem_set__product').distinct()

    # Filter to only orders that contain this vendor's products
    # Since Order doesn't have direct vendor FK, we use Payment which links to Order
    # Get all completed payments for orders containing vendor products
    completed_payments = Payment.objects.filter(
        paymentStatus='Completed',
        order__isnull=False
    ).select_related('order')

    # Total revenue = sum of all completed order amounts for this vendor
    # (Approximation: filter orders where customer bought vendor products)
    total_revenue = sum(
        p.order.totalAmount for p in completed_payments
        if Product.objects.filter(vendor=vendor, price=p.order.totalAmount).exists()
    )

    # Payment method breakdown
    payment_methods = {}
    for p in completed_payments:
        method = p.paymentType or 'razorpay'
        payment_methods[method] = payment_methods.get(method, 0) + 1

    # Total orders count for this vendor
    total_orders = completed_payments.count()

    # Recent transactions (last 10)
    recent_transactions = completed_payments.order_by('-order__orderDate')[:10]

    # Low stock products (stock < 5)
    low_stock_products = products.filter(stock__lt=5, stock__gt=0).order_by('stock')
    out_of_stock = products.filter(stock=0).count()

    # 7. Render
    return render(request, "Vendors/vendors.html", {
        "vendor": vendor,
        "products": products,
        "labels": labels,
        "chart_data": chart_data,
        "total_views": total_views,
        "total_stock": total_stock,
        "query": query,
        # Accounting data
        "total_revenue":       total_revenue,
        "total_orders":        total_orders,
        "payment_methods":     payment_methods,
        "recent_transactions": recent_transactions,
        "low_stock_products":  low_stock_products,
        "out_of_stock":        out_of_stock,
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
    
    # 1. Create a list for unique gallery images
    unique_gallery = []
    seen_urls = set()
    
    # 2. Add the main product image first to 'seen' so it isn't duplicated
    if product.product_image:
        seen_urls.add(product.product_image.url)

    # 3. Loop through all variants and only add new, unique images
    for variant in product.variants.all():
        if variant.image:
            img_url = variant.image.url
            if img_url not in seen_urls:
                unique_gallery.append(img_url)
                seen_urls.add(img_url)

    return render(request, "Customers/product_detail.html", {
        "product": product,
        "unique_gallery": unique_gallery, # This list now contains NO duplicates
    })

# ════════════════════════════════════════════
# RAZORPAY — Step 1: Create order & open checkout
# Called when customer clicks "Buy Now"
# ════════════════════════════════════════════
def initiate_payment(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # 1. Get the Customer instance linked to the current User
    # Assuming your Customer model has a 'user' field or matches request.user
    try:
        customer_profile = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        # Fallback if the profile isn't found
        return render(request, 'Customers/error.html', {'message': 'Customer profile not found.'})

    # 2. Razorpay Setup
    amount_paise = int(product.price * 100)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    data = {
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": "1"
    }
    razorpay_order = client.order.create(data=data)

    # 3. Create Internal Order (Matching your exact Model names)
    order = Order.objects.create(
        customer    = customer_profile, # Uses 'customer' from your model
        status      = 'Pending',
        totalAmount = product.price     # Uses 'totalAmount' from your model
    )

    # 4. Create Payment Record
    Payment.objects.create(
        order             = order,
        paymentType       = 'razorpay',
        paymentStatus     = 'Pending',
        razorpay_order_id = razorpay_order['id'],
    )

    # 5. UI Context
    context = {
        'product':           product,
        'order':             order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key':      settings.RAZORPAY_KEY_ID,
        'amount':            amount_paise,
        'amount_display':    product.price,
        'customer_name':     getattr(customer_profile, 'name', 'Customer'), # Adjust based on Customer model
        'customer_email':    getattr(request.user, 'email', ''),
    }
 
    return render(request, 'Customers/payment.html', context)
# ════════════════════════════════════════════
# RAZORPAY — Step 2: Verify payment after success
# Called by Razorpay after payment is completed
# ════════════════════════════════════════════
@csrf_exempt
@login_required
def payment_success(request):
    if request.method == 'POST':
        # 1. Get the data from Razorpay POST request
        params_dict = {
            'razorpay_order_id': request.POST.get('razorpay_order_id', ''),
            'razorpay_payment_id': request.POST.get('razorpay_payment_id', ''),
            'razorpay_signature': request.POST.get('razorpay_signature', '')
        }

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # 2. Use the official Razorpay utility to verify
            client.utility.verify_payment_signature(params_dict)
            
            # 3. If verified, update your database
            payment = Payment.objects.get(razorpay_order_id=params_dict['razorpay_order_id'])
            order = payment.order

            payment.razorpay_payment_id = params_dict['razorpay_payment_id']
            payment.razorpay_signature = params_dict['razorpay_signature']
            payment.paymentStatus = 'Completed'
            payment.save()

            order.status = 'Confirmed'
            order.save()

            return render(request, 'Customers/payment_success.html', {'order': order, 'payment': payment})

        except (razorpay.errors.SignatureVerificationError, Payment.DoesNotExist):
            # 4. Handle failure/tampering
            if 'razorpay_order_id' in params_dict:
                payment = Payment.objects.filter(razorpay_order_id=params_dict['razorpay_order_id']).first()
                if payment:
                    payment.paymentStatus = 'Failed'
                    payment.save()
                    payment.order.status = 'Failed'
                    payment.order.save()
            
            return render(request, 'Customers/payment_failed.html')

    return redirect('customer_dashboard')
# ════════════════════════════════════════════
# RAZORPAY — Step 3: Handle payment failure
# ════════════════════════════════════════════
def payment_failed(request):
    return render(request, 'Customers/payment_failed.html', {'order': None})