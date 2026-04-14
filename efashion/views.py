from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum
from.models import Vendor, Customer, Product, Order, Color, Size, ProductVariant
# Importing forms and models from your apps
from .forms import SignupForm, LoginForm
from efashion.models import Vendor, Customer, Product, Order, Color, Size, ProductVariant, Payment, Review, ContactMessage
from efashion.forms import VendorProfileForm, CustomerProfileForm
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
import razorpay
import hmac
import hashlib
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
import random

PLATFORM_COMMISSION_RATE = 0.25
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

                if user.is_superuser or user.role == "admin":
                    return redirect("admin_dashboard")
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


def forgot_password(request):
    if request.method != "POST":
        return redirect("login")

    form = LoginForm()
    user_model = get_user_model()
    step = request.POST.get("step")

    if step == "send_email":
        email = request.POST.get("email", "").strip().lower()
        user = user_model.objects.filter(email__iexact=email).first()

        if not user:
            messages.error(request, "No account was found with that email address.")
            return render(request, "login.html", {"form": form})

        otp = f"{random.randint(100000, 999999)}"
        request.session["password_reset_email"] = user.email
        request.session["password_reset_otp"] = otp
        request.session["password_reset_verified"] = False

        try:
            send_mail(
                "WearWeb Password Reset OTP",
                f"Your OTP for resetting your password is {otp}.",
                getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
                [user.email],
                fail_silently=False,
            )
            messages.success(request, "We sent an OTP to your email address.")
        except Exception:
            messages.error(request, "We couldn't send the reset email right now. Please try again.")
            return render(request, "login.html", {"form": form})

        return render(
            request,
            "login.html",
            {
                "form": form,
                "show_otp_step": True,
                "otp_email": user.email,
            },
        )

    if step == "verify_otp":
        email = request.POST.get("email", "").strip().lower()
        otp = request.POST.get("otp", "").strip()
        session_email = request.session.get("password_reset_email", "").lower()
        session_otp = request.session.get("password_reset_otp")

        if email != session_email or otp != session_otp:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(
                request,
                "login.html",
                {
                    "form": form,
                    "show_otp_step": True,
                    "otp_email": email or session_email,
                },
            )

        request.session["password_reset_verified"] = True
        messages.success(request, "OTP verified. You can set a new password now.")
        return render(
            request,
            "login.html",
            {
                "form": form,
                "show_new_password_step": True,
                "reset_email": session_email,
                "verified_otp": session_otp,
            },
        )

    if step == "reset_password":
        email = request.POST.get("email", "").strip().lower()
        otp = request.POST.get("otp", "").strip()
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")
        session_email = request.session.get("password_reset_email", "").lower()
        session_otp = request.session.get("password_reset_otp")
        is_verified = request.session.get("password_reset_verified", False)

        if email != session_email or otp != session_otp or not is_verified:
            messages.error(request, "Password reset session expired. Please start again.")
            return render(request, "login.html", {"form": form})

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(
                request,
                "login.html",
                {
                    "form": form,
                    "show_new_password_step": True,
                    "reset_email": session_email,
                    "verified_otp": session_otp,
                },
            )

        user = user_model.objects.filter(email__iexact=session_email).first()
        if not user:
            messages.error(request, "No account was found for this reset request.")
            return render(request, "login.html", {"form": form})

        user.set_password(new_password)
        user.save()
        request.session.pop("password_reset_email", None)
        request.session.pop("password_reset_otp", None)
        request.session.pop("password_reset_verified", None)
        messages.success(request, "Password reset successful. Please log in.")
        return redirect("login")

    messages.error(request, "Invalid password reset request.")
    return redirect("login")

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
    customer = Customer.objects.filter(user=request.user).first()
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True).order_by('-created_at')[:12]
    return render(request, "Customers/customers.html", {
        "customer": customer,
        "new_arrivals": new_arrivals,
    })

@login_required
def customer_profile(request):
    """ Displays stats and orders. Button here links to complete_profile for ccp.html """
    customer = get_object_or_404(Customer, user=request.user)
    orders = (
        Order.objects
        .filter(customer=customer)
        .exclude(status='Cancelled')
        .select_related('product')
        .order_by('-orderDate', '-id')
    )
    return render(request, 'Customers/customer_profile.html', {
        'customer': customer,
        'orders': orders,
        'order_count': orders.count(),
    })


def build_shop_context(request, base_products, category_name="All Products", selected_category=None):
    selected_colors = [color.strip() for color in request.GET.getlist('color') if color.strip()]
    price_range = request.GET.get('p')

    filtered_products = base_products
    if selected_colors:
        filtered_products = filtered_products.filter(variants__color__name__in=selected_colors).distinct()

    if price_range == 'below-999':
        filtered_products = filtered_products.filter(price__lt=999)
    elif price_range == '1000-2000':
        filtered_products = filtered_products.filter(price__gte=1000, price__lte=2000)
    elif price_range == 'above-2000':
        filtered_products = filtered_products.filter(price__gt=2000)

    color_names = (
        ProductVariant.objects
        .filter(product__in=base_products, color__isnull=False)
        .values_list('color__name', flat=True)
        .distinct()
        .order_by('color__name')
    )

    return {
        'products': filtered_products.order_by('-id'),
        'category_name': category_name,
        'selected_colors': selected_colors,
        'selected_price_range': price_range,
        'selected_category': selected_category,
        'available_colors': [{'name': color_name} for color_name in color_names],
    }


def search_view(request):
    query = request.GET.get('q', '').strip()
    results = Product.objects.none()
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(vendor__shopname__icontains=query)
        ).filter(is_active=True).select_related('vendor')
    context = build_shop_context(
        request,
        results,
        category_name=f'Search: "{query}"' if query else 'All Products',
    )
    context['query'] = query
    return render(request, 'Customers/shop_all.html', context)

@login_required
def my_orders(request):
    customer = get_object_or_404(Customer, user=request.user)
    orders = (
        Order.objects
        .filter(customer=customer)
        .exclude(status='Cancelled')
        .select_related('product')
        .order_by('-orderDate', '-id')
    )
    return render(request, 'Customers/myorders.html', {
        'orders': orders,
    })


@login_required
@require_POST
def cancel_order(request, order_id):
    customer = get_object_or_404(Customer, user=request.user)
    order = get_object_or_404(Order, id=order_id, customer=customer)

    if order.status in ['Pending', 'Confirmed']:
        order.status = 'Cancelled'
        order.save(update_fields=['status'])

        payment = order.payment_set.first()
        if payment:
            payment.paymentStatus = 'Refund Pending' if payment.paymentStatus == 'Completed' else 'Cancelled'
            payment.save(update_fields=['paymentStatus'])

        adjust_order_stock(order, increase=True)
        messages.success(request, f"Order #{order.id} has been cancelled.")
    else:
        messages.warning(request, "Only pending or confirmed orders can be cancelled.")

    return redirect('my_orders')

def brand_product_view(request, brand_name, cat_slug=None): # Use 'cat_slug' here
    # 1. Base filter for the brand
    products = Product.objects.filter(brand_name__iexact=brand_name, is_active=True)
    
    # 2. Check if the user wants 'both' or a specific category
    if cat_slug == 'both':
        # This shows both 'mens' and 'womens' clothing for that brand
        products = products.filter(category__in=['mens', 'womens'])
        display_title = f"{brand_name} (Men & Women)"
    elif cat_slug:
        # Standard filter for single category
        products = products.filter(category__iexact=cat_slug)
        display_title = f"{brand_name} {cat_slug.title()}"
    else:
        display_title = brand_name.title()

    return render(request, "Customers/brand_all.html", {
        "products": products,
        "brand_name": display_title,
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
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name', '').strip(),
            email=request.POST.get('email', '').strip(),
            subject=request.POST.get('subject') or 'other',
            message=request.POST.get('message', '').strip(),
        )
        messages.success(request, "Your message has been sent successfully.")
        return redirect('contact_us')
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

    context = build_shop_context(
        request,
        products,
        category_name=display_name,
        selected_category=cat_slug,
    )
    return render(request, "Customers/shop_all.html", context)

def shop_all(request):
    products = Product.objects.filter(is_active=True).prefetch_related('variants__color')

    cat = request.GET.get('category')
    if cat:
        products = products.filter(category=cat)

    category_labels = dict(Product.CATEGORY_CHOICES)
    context = build_shop_context(
        request,
        products,
        category_name=category_labels.get(cat, "All Products"),
        selected_category=cat,
    )
    return render(request, 'Customers/shop_all.html', context)

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
    vendor_orders = Order.objects.filter(
        product__vendor=vendor
    ).select_related('product', 'customer__user').prefetch_related('payment_set').order_by('-orderDate', '-id')

    completed_payments = Payment.objects.filter(
        paymentStatus='Completed',
        order__product__vendor=vendor,
        order__isnull=False
    ).select_related('order', 'order__product')

    total_revenue = sum(p.order.totalAmount for p in completed_payments)
    ramya_commission = total_revenue * PLATFORM_COMMISSION_RATE
    vendor_net_revenue = total_revenue - ramya_commission

    # Payment method breakdown
    payment_methods = {}
    for p in completed_payments:
        method = p.paymentType or 'razorpay'
        payment_methods[method] = payment_methods.get(method, 0) + 1

    # Total orders count for this vendor
    total_orders = vendor_orders.exclude(status='Cancelled').count()

    # Recent transactions (last 10)
    recent_transactions = vendor_orders[:10]

    product_reviews = Review.objects.filter(
        product__vendor=vendor
    ).select_related('product', 'customer__user').order_by('-id')[:12]

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
        "ramya_commission":    ramya_commission,
        "vendor_net_revenue":  vendor_net_revenue,
        "total_orders":        total_orders,
        "payment_methods":     payment_methods,
        "recent_transactions": recent_transactions,
        "low_stock_products":  low_stock_products,
        "out_of_stock":        out_of_stock,
        "product_reviews":     product_reviews,
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
        qtys = request.POST.getlist('variant_qty[]')
        try:
            total_stock = sum(int(q) for q in qtys if q not in [None, ''])
        except ValueError:
            total_stock = product.stock or 0

        sub_category_value = request.POST.get('sub_category') or product.sub_category
        sub_category_aliases = {
            'jacket': 'jackets',
            't-shirt': 'tshirts',
            'shirt': 'shirts',
            'hoodie': 'hoodies',
            'pant': 'womenpants' if request.POST.get('category') == 'womens' else 'menpants',
            'traditional': 'traditional',
            'saree': 'saree',
            'kurti': 'kurti',
            'western': 'western',
            'sweatshirt': 'sweatshirts',
            'boys': 'boys',
            'girls': 'girls',
        }

        product.name = request.POST.get('name')
        product.brand_name = request.POST.get('brand')
        product.category = request.POST.get('category')
        product.price = request.POST.get('price')
        product.sub_category = sub_category_aliases.get(sub_category_value, sub_category_value)
        product.original_price = request.POST.get('original_price') or None
        product.stock = total_stock
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
        # 1. Collect Parent Product Form Data
        name = request.POST.get('name')
        category = request.POST.get('category')
        sub_category = request.POST.get('sub_category')
        price = request.POST.get('price')
        description = request.POST.get('description')
        brand = request.POST.get('brand', 'Generic')

        # 2. Collect Variant Lists (from dynamic table rows)
        color_names = request.POST.getlist('variant_color_name[]')
        color_codes = request.POST.getlist('variant_color_code[]')
        color_groups = request.POST.getlist('variant_color_group[]')
        size_groups = request.POST.getlist('variant_group[]')
        sizes = request.POST.getlist('variant_size[]')
        qtys = request.POST.getlist('variant_qty[]')
        variant_photos = request.FILES.getlist('variant_image[]')

        # 3. Validation & Prep
        # Calculate total stock by summing all quantities provided
        try:
            total_stock = sum(int(q) for q in qtys if q)
        except ValueError:
            total_stock = 0
            
        # Use the very first image uploaded in the variants as the primary photo
        main_product_photo = variant_photos[0] if variant_photos else None

        color_map = {}
        for index, group_id in enumerate(color_groups):
            if not group_id:
                continue
            color_map[group_id] = {
                'name': color_names[index].strip() if index < len(color_names) else '',
                'code': color_codes[index].strip() if index < len(color_codes) else '',
                'image': variant_photos[index] if index < len(variant_photos) else None,
            }

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
            product_image=main_product_photo,
            is_active=True
        )

        # 5. Create Variants (REPAIRED LOOP)
        # We loop through 'sizes' because that represents the total number of rows.
        for i in range(len(sizes)):
            # Check if this row has at least a size or a quantity
            if sizes[i] or (i < len(qtys) and qtys[i]):
                current_group = size_groups[i] if i < len(size_groups) else None
                current_color = color_map.get(current_group, {})
                current_color_name = current_color.get('name')
                current_color_code = current_color.get('code')

                # Handle Foreign Keys (Get or Create)
                c_obj = None
                if current_color_name:
                    c_obj, _ = Color.objects.get_or_create(
                        name=current_color_name.strip().title(),
                        defaults={'code': current_color_code or None}
                    )
                    if current_color_code and c_obj.code != current_color_code:
                        c_obj.code = current_color_code
                        c_obj.save(update_fields=['code'])
                
                s_obj = None
                if sizes[i]:
                    s_obj, _ = Size.objects.get_or_create(name=sizes[i].strip().upper())
                
                # Reuse the image uploaded for the current colour block
                v_photo = current_color.get('image')
                
                # Get the quantity for this specific size
                row_qty = int(qtys[i]) if (i < len(qtys) and qtys[i]) else 0

                # Create the Variant entry in the database
                ProductVariant.objects.create(
                    product=product,
                    color=c_obj,
                    size=s_obj,
                    variant_stock=row_qty,
                    image=v_photo
                )

        messages.success(request, f'Product "{name}" published with all variants!')
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

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to submit a review.")
            return redirect("login")

        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            messages.error(request, "Only customers can submit reviews.")
            return redirect("product_detail", pk=pk)

        try:
            rating = int(request.POST.get("rating", "0"))
        except (TypeError, ValueError):
            rating = 0

        comment = request.POST.get("comment", "").strip()

        if rating < 1 or rating > 5:
            messages.error(request, "Please choose a rating between 1 and 5.")
            return redirect("product_detail", pk=pk)

        Review.objects.update_or_create(
            customer=customer,
            product=product,
            defaults={
                "rating": rating,
                "comment": comment,
            },
        )
        messages.success(request, "Your review was submitted successfully.")
        return redirect("product_detail", pk=pk)

    product.increment_views()
    
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


def adjust_order_stock(order, increase=False):
    product = order.product
    if not product:
        return

    new_stock = product.stock + (1 if increase else -1)
    product.stock = max(new_stock, 0)
    product.save(update_fields=['stock'])


def finalize_payment(payment, payment_id, signature, payment_type='razorpay'):
    order = payment.order

    if payment.paymentStatus != 'Completed':
        payment.paymentStatus = 'Completed'
        payment.paymentType = payment_type
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.save()

        order.status = 'Confirmed'
        order.save(update_fields=['status'])
        adjust_order_stock(order, increase=False)

    return order

# ════════════════════════════════════════════
# RAZORPAY — Cart Checkout
# ════════════════════════════════════════════
@login_required
def initiate_cart_payment(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('view_cart')

    customer_profile = get_object_or_404(Customer, user=request.user)
    cart_items = []
    total_price = 0

    for product_id, item_data in cart.items():
        product = get_object_or_404(Product, id=product_id, is_active=True)
        quantity = max(int(item_data.get('quantity', 1)), 1)
        line_total = product.price * quantity
        total_price += line_total
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
        })

    context = {
        'cart_items': cart_items,
        'is_cart_checkout': True,
        'checkout_title': f'Cart Checkout ({sum(item["quantity"] for item in cart_items)} items)',
        'amount_display': total_price,
        'customer_name': getattr(customer_profile, 'name', 'Customer'),
        'customer_email': getattr(request.user, 'email', ''),
        'current_address': customer_profile.address or '',
        'delivery_address': customer_profile.address or '',
    }

    if request.method == 'POST':
        use_current_address = request.POST.get('use_current_address') == '1'
        delivery_address = (customer_profile.address if use_current_address else request.POST.get('delivery_address', '')).strip()

        if len(delivery_address) < 10:
            messages.error(request, "Please enter the full delivery address.")
            context['use_current_address'] = use_current_address
            context['delivery_address'] = delivery_address
            return render(request, 'Customers/payment.html', context)

        amount_paise = int(total_price * 100)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create(data={
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": "1"
        })

        created_order_ids = []
        created_orders = []
        for item in cart_items:
            for _ in range(item['quantity']):
                order = Order.objects.create(
                    customer=customer_profile,
                    product=item['product'],
                    status='Pending',
                    totalAmount=item['product'].price,
                    delivery_address=delivery_address,
                )
                Payment.objects.create(
                    order=order,
                    paymentType='razorpay',
                    paymentStatus='Pending',
                    razorpay_order_id=razorpay_order['id'],
                )
                created_order_ids.append(order.id)
                created_orders.append(order)

        request.session['pending_cart_checkout_razorpay_order_id'] = razorpay_order['id']
        request.session['pending_cart_checkout_order_ids'] = created_order_ids

        context.update({
            'checkout_reference': f'CART-{razorpay_order["id"]}',
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'callback_url': request.build_absolute_uri(reverse('payment_success')),
            'amount': amount_paise,
            'ready_to_pay': True,
            'order': created_orders[0] if created_orders else None,
            'delivery_address': delivery_address,
            'use_current_address': use_current_address,
        })
        messages.success(request, "Delivery address saved. You can complete the payment now.")

    return render(request, 'Customers/payment.html', context)

# ════════════════════════════════════════════
# RAZORPAY — Step 1: Create order & open checkout
# Called when customer clicks "Buy Now"
# ════════════════════════════════════════════
@login_required
def initiate_payment(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # 1. Get the Customer instance linked to the current User
    # Assuming your Customer model has a 'user' field or matches request.user
    try:
        customer_profile = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        # Fallback if the profile isn't found
        return render(request, 'Customers/error.html', {'message': 'Customer profile not found.'})

    context = {
        'product': product,
        'amount_display': product.price,
        'customer_name': getattr(customer_profile, 'name', 'Customer'),
        'customer_email': getattr(request.user, 'email', ''),
        'current_address': customer_profile.address or '',
        'delivery_address': customer_profile.address or '',
    }

    if request.method == 'POST':
        use_current_address = request.POST.get('use_current_address') == '1'
        delivery_address = (customer_profile.address if use_current_address else request.POST.get('delivery_address', '')).strip()

        if len(delivery_address) < 10:
            messages.error(request, "Please enter the full delivery address.")
            context['use_current_address'] = use_current_address
            context['delivery_address'] = delivery_address
            return render(request, 'Customers/payment.html', context)

        amount_paise = int(product.price * 100)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create(data={
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": "1"
        })

        order = Order.objects.create(
            customer=customer_profile,
            product=product,
            status='Pending',
            totalAmount=product.price,
            delivery_address=delivery_address,
        )

        Payment.objects.create(
            order=order,
            paymentType='razorpay',
            paymentStatus='Pending',
            razorpay_order_id=razorpay_order['id'],
        )

        context.update({
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'callback_url': request.build_absolute_uri(reverse('payment_success')),
            'amount': amount_paise,
            'ready_to_pay': True,
            'delivery_address': delivery_address,
            'use_current_address': use_current_address,
        })
        messages.success(request, "Delivery address saved. You can complete the payment now.")

    return render(request, 'Customers/payment.html', context)
# ════════════════════════════════════════════
# RAZORPAY — Step 2: Verify payment after success
# Called by Razorpay after payment is completed
# ════════════════════════════════════════════
@csrf_exempt
def payment_success(request):
    if request.method in ['POST', 'GET']:
        # 1. Get the data from Razorpay POST request
        params_dict = {
            'razorpay_order_id': request.POST.get('razorpay_order_id', ''),
            'razorpay_payment_id': request.POST.get('razorpay_payment_id', ''),
            'razorpay_signature': request.POST.get('razorpay_signature', '')
        }
        if request.method == 'GET':
            params_dict = {
                'razorpay_order_id': request.GET.get('razorpay_order_id', ''),
                'razorpay_payment_id': request.GET.get('razorpay_payment_id', ''),
                'razorpay_signature': request.GET.get('razorpay_signature', '')
            }

        if not params_dict['razorpay_payment_id']:
            failed_order_id = request.POST.get('order_id') or request.GET.get('order_id')
            if failed_order_id:
                failed_order = Order.objects.filter(id=failed_order_id).first()
                if failed_order:
                    failed_order.status = 'Failed'
                    failed_order.save(update_fields=['status'])
                    failed_payment = failed_order.payment_set.first()
                    if failed_payment and failed_payment.paymentStatus != 'Completed':
                        failed_payment.paymentStatus = 'Failed'
                        failed_payment.save(update_fields=['paymentStatus'])
            return render(request, 'Customers/payment_fail.html')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # 2. Use the official Razorpay utility to verify
            client.utility.verify_payment_signature(params_dict)
            
            # 3. If verified, update your database
            payments = list(Payment.objects.filter(
                razorpay_order_id=params_dict['razorpay_order_id']
            ).select_related('order', 'order__product'))

            if not payments:
                raise Payment.DoesNotExist

            completed_orders = []
            for payment in payments:
                completed_orders.append(
                    finalize_payment(
                        payment,
                        params_dict['razorpay_payment_id'],
                        params_dict['razorpay_signature'],
                        payment_type='razorpay',
                    )
                )

            if request.session.get('pending_cart_checkout_razorpay_order_id') == params_dict['razorpay_order_id']:
                request.session['cart'] = {}
                request.session.pop('pending_cart_checkout_razorpay_order_id', None)
                request.session.pop('pending_cart_checkout_order_ids', None)

            primary_order = completed_orders[0]
            primary_payment = payments[0]
            return render(request, 'Customers/payment_success.html', {
                'order': primary_order,
                'orders': completed_orders,
                'payment': primary_payment,
                'amount_paid': sum(order.totalAmount for order in completed_orders),
            })

        except (razorpay.errors.SignatureVerificationError, Payment.DoesNotExist):
            # 4. Handle failure/tampering
            if 'razorpay_order_id' in params_dict:
                payment = Payment.objects.filter(razorpay_order_id=params_dict['razorpay_order_id']).first()
                if payment:
                    payment.paymentStatus = 'Failed'
                    payment.save()
                    payment.order.status = 'Failed'
                    payment.order.save()
            
            return render(request, 'Customers/payment_fail.html')

    return redirect('customer_dashboard')
# ════════════════════════════════════════════
# RAZORPAY — Step 3: Handle payment failure
# ════════════════════════════════════════════
def payment_failed(request):
    return render(request, 'Customers/payment_fail.html', {'order': None})


# ════════════════════════════════════════════
# DUMMY PAYMENT — skips Razorpay, marks paid
# For development/demo only
# ════════════════════════════════════════════
@login_required
def dummy_payment(request, order_id):
    import uuid
    order = get_object_or_404(Order, id=order_id)

    # Only the customer who placed this order can pay
    if order.customer.user != request.user:
        return redirect('customer_dashboard')

    # Get or find the pending payment for this order
    payment = Payment.objects.filter(order=order, paymentStatus='Pending').first()

    if payment:
        payment.razorpay_order_id   = payment.razorpay_order_id or ('DEMO_ORD_' + uuid.uuid4().hex[:12].upper())
        order = finalize_payment(
            payment,
            'DEMO_PAY_' + uuid.uuid4().hex[:12].upper(),
            'DEMO_SIG_' + uuid.uuid4().hex[:16].upper(),
            payment_type='demo',
        )

        return render(request, 'Customers/payment_success.html', {
            'order':   order,
            'payment': payment,
        })

    # No pending payment found
    return redirect('customer_dashboard')

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)
 
admin_required = user_passes_test(is_admin, login_url='login')
 
 
# ════════════════════════════════════════════════════
# 1. ADMIN DASHBOARD — overview of everything
# ════════════════════════════════════════════════════
@login_required
@admin_required
def admin_dashboard(request):
    # ── Counts ──
    total_vendors   = Vendor.objects.count()
    total_customers = Customer.objects.count()
    total_products  = Product.objects.count()
    total_orders    = Order.objects.count()
 
    # ── Revenue ──
    total_revenue = Payment.objects.filter(
        paymentStatus='Completed'
    ).aggregate(rev=Sum('order__totalAmount'))['rev'] or 0
    ramya_revenue = total_revenue * PLATFORM_COMMISSION_RATE
    vendor_payout_total = total_revenue - ramya_revenue
    completed_transactions = Payment.objects.filter(paymentStatus='Completed').count()
 
    pending_orders = Order.objects.filter(status='Pending').count()
 
    # ── Recent orders (last 8) ──
    recent_orders = Order.objects.select_related(
        'customer__user'
    ).prefetch_related('payment_set').order_by('-orderDate')[:8]
 
    # ── New vendors (last 7 days) ──
    week_ago = timezone.now() - timedelta(days=7)
    new_vendors = Vendor.objects.filter(user__date_joined__gte=week_ago).count()
    new_customers = Customer.objects.filter(user__date_joined__gte=week_ago).count()
    new_vendors = Vendor.objects.filter(user__date_joined__gte=week_ago).count()
    new_customers = Customer.objects.filter(user__date_joined__gte=week_ago).count()
    # ── Top products by views ──
    top_products = Product.objects.select_related('vendor').order_by('-view_count')[:5]
 
    # ── Payment method breakdown ──
    pay_methods = Payment.objects.filter(
        paymentStatus='Completed'
    ).values('paymentType').annotate(count=Count('id')).order_by('-count')
 
    # ── Low stock ──
    low_stock = Product.objects.filter(stock__lt=5, is_active=True).count()
 
    return render(request, 'Admin/admin_dashboard.html', {
        'total_vendors':   total_vendors,
        'total_customers': total_customers,
        'total_products':  total_products,
        'total_orders':    total_orders,
        'total_revenue':   total_revenue,
        'ramya_revenue':   ramya_revenue,
        'vendor_payout_total': vendor_payout_total,
        'completed_transactions': completed_transactions,
        'pending_orders':  pending_orders,
        'recent_orders':   recent_orders,
        'new_vendors':     new_vendors,
        'new_customers':   new_customers,
        'top_products':    top_products,
        'pay_methods':     pay_methods,
        'low_stock':       low_stock,
    })


@login_required
@admin_required
def admin_finance(request):
    completed_payments = Payment.objects.filter(
        paymentStatus='Completed'
    ).select_related('order', 'order__product', 'order__product__vendor')

    gross_sales = sum(payment.order.totalAmount for payment in completed_payments if payment.order)
    ramya_revenue = gross_sales * PLATFORM_COMMISSION_RATE
    vendor_payout_total = gross_sales - ramya_revenue

    finance_rows = []
    for payment in completed_payments.order_by('-order__orderDate', '-id')[:50]:
        if not payment.order:
            continue
        gross_amount = payment.order.totalAmount
        commission = gross_amount * PLATFORM_COMMISSION_RATE
        net_amount = gross_amount - commission
        finance_rows.append({
            'payment': payment,
            'gross_amount': gross_amount,
            'commission': commission,
            'net_amount': net_amount,
        })

    return render(request, 'Admin/admin_finance.html', {
        'gross_sales': gross_sales,
        'ramya_revenue': ramya_revenue,
        'vendor_payout_total': vendor_payout_total,
        'completed_transactions': completed_payments.count(),
        'finance_rows': finance_rows,
    })


@login_required
@admin_required
def admin_messages(request):
    contact_messages = ContactMessage.objects.all()
    return render(request, 'Admin/admin_messages.html', {
        'contact_messages': contact_messages,
    })
 
 
# ════════════════════════════════════════════════════
# 2. VENDORS — list, approve, block
# ════════════════════════════════════════════════════
@login_required
@admin_required
def admin_vendors(request):
    query   = request.GET.get('q', '').strip()
    vendors = Vendor.objects.select_related('user').annotate(
        product_count=Count('product')
    ).order_by('-user__date_joined')
 
    if query:
        vendors = vendors.filter(
            Q(shopname__icontains=query) |
            Q(user__email__icontains=query)
        )
 
    return render(request, 'Admin/admin_vendors.html', {
        'vendors': vendors,
        'query':   query,
    })
 
 
@login_required
@admin_required
@require_POST
def admin_toggle_vendor(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.user.is_active = not vendor.user.is_active
    vendor.user.save()
    status = 'activated' if vendor.user.is_active else 'blocked'
    messages.success(request, f"Vendor '{vendor.shopname}' {status}.")
    return redirect('admin_vendors')
 
 
@login_required
@admin_required
@require_POST
def admin_delete_vendor(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    name   = vendor.shopname
    vendor.user.delete()   # cascades to Vendor
    messages.warning(request, f"Vendor '{name}' deleted permanently.")
    return redirect('admin_vendors')
 
 
# ════════════════════════════════════════════════════
# 3. CUSTOMERS — list, block
# ════════════════════════════════════════════════════
@login_required
@admin_required
def admin_customers(request):
    query     = request.GET.get('q', '').strip()
    customers = Customer.objects.select_related('user').annotate(
        order_count=Count('order')
    ).order_by('-user__date_joined')
 
    if query:
        customers = customers.filter(
            Q(user__email__icontains=query) |
            Q(address__icontains=query)
        )
 
    return render(request, 'Admin/admin_customers.html', {
        'customers': customers,
        'query':     query,
    })
 
 
@login_required
@admin_required
@require_POST
def admin_toggle_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.user.is_active = not customer.user.is_active
    customer.user.save()
    status = 'activated' if customer.user.is_active else 'blocked'
    messages.success(request, f"Customer {customer.user.email} {status}.")
    return redirect('admin_customers')
 
 
# ════════════════════════════════════════════════════
# 4. PRODUCTS — list, approve, delete
# ════════════════════════════════════════════════════
@login_required
@admin_required
def admin_products(request):
    query    = request.GET.get('q', '').strip()
    category = request.GET.get('cat', '').strip()
    products = Product.objects.select_related('vendor').order_by('-created_at')
 
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(vendor__shopname__icontains=query)
        )
    if category:
        products = products.filter(category=category)
 
    return render(request, 'Admin/admin_products.html', {
        'products':         products,
        'query':            query,
        'selected_cat':     category,
        'category_choices': Product.CATEGORY_CHOICES,
    })
 
 
@login_required
@admin_required
@require_POST
def admin_toggle_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    return JsonResponse({'status': 'ok', 'is_active': product.is_active})
 
 
@login_required
@admin_required
@require_POST
def admin_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name    = product.name
    product.delete()
    messages.warning(request, f"Product '{name}' deleted.")
    return redirect('admin_products')
 
 
# ════════════════════════════════════════════════════
# 5. ORDERS — list, update status
# ════════════════════════════════════════════════════
@login_required
@admin_required
def admin_orders(request):
    status_filter = request.GET.get('status', '').strip()
    orders = Order.objects.select_related(
        'customer__user', 'product'
    ).prefetch_related('payment_set').order_by('-orderDate')
    if status_filter:
        orders = orders.filter(status=status_filter)
 
    STATUS_CHOICES = ['Pending', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled', 'Failed']
 
    return render(request, 'Admin/admin_orders.html', {
        'orders':         orders,
        'status_filter':  status_filter,
        'status_choices': STATUS_CHOICES,
    })


@login_required
@admin_required
@require_POST
def admin_delete_order(request, pk):
    order = get_object_or_404(Order, pk=pk, status='Cancelled')
    order.delete()
    messages.warning(request, f"Cancelled order #{pk} deleted.")
    return redirect(request.POST.get('next') or 'admin_orders')
 
 
@login_required
@admin_required
@require_POST
def admin_update_order_status(request, pk):
    order      = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')
    STATUS_CHOICES = ['Pending', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled', 'Failed']
    if new_status in STATUS_CHOICES:
        previous_status = order.status
        order.status = new_status
        order.save()

        if previous_status != 'Cancelled' and new_status == 'Cancelled':
            adjust_order_stock(order, increase=True)
            payment = order.payment_set.first()
            if payment:
                payment.paymentStatus = 'Refund Pending' if payment.paymentStatus == 'Completed' else 'Cancelled'
                payment.save(update_fields=['paymentStatus'])
        elif previous_status == 'Cancelled' and new_status != 'Cancelled':
            adjust_order_stock(order, increase=False)

        messages.success(request, f"Order #{order.id} status updated to {new_status}.")
    return redirect('admin_orders')
 
 
# ════════════════════════════════════════════════════
# 6. REVIEWS — list, delete spam
# ════════════════════════════════════════════════════
@login_required
@admin_required
def admin_reviews(request):
    reviews = Review.objects.select_related(
        'customer__user', 'product'
    ).order_by('-id')
    return render(request, 'Admin/admin_reviews.html', {'reviews': reviews})
 
 
@login_required
@admin_required
@require_POST
def admin_delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.warning(request, "Review deleted.")
    return redirect('admin_reviews')
