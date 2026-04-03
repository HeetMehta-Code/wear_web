from django.urls import path
from django.contrib import admin
from efashion import views as efashion_views 
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- AUTH & REGISTRATION ---
    path("", efashion_views.signup_view, name="signup"),
    path("login/", efashion_views.login_view, name="login"),
    path("logout/", efashion_views.logout_view, name="logout"),
    
    # This remains the path for ccp.html (Customer) and cvp.html (Vendor initial setup)
    path("complete-profile/", efashion_views.complete_profile, name="complete_profile"),

    # --- CUSTOMER FLOW ---
    path("customer-dashboard/", efashion_views.customer_dashboard, name="customer_dashboard"),
    # This opens customer_profile.html (The View/Stats page)
    path("customer-profile/", efashion_views.customer_profile, name="customer_profile"),
    path('search/', efashion_views.search_view, name='search_products'),
    path('my-orders/', efashion_views.my_orders, name='my_orders'),
    path('brand/<str:brand_name>/', efashion_views.brand_product_view, name='brand_products'),
    path('collection/<str:feature_type>/', efashion_views.feature_collection_view, name='feature_collection'),
    path('about/', efashion_views.about_us, name='about_us'),
    path('contact/', efashion_views.contact_us, name='contact_us'),
    path('category/<str:cat_slug>/', efashion_views.category_view, name='category_view'),
    path('cart/', efashion_views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', efashion_views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', efashion_views.remove_from_cart, name='remove_from_cart'),
    # --- VENDOR FLOW ---
     path("vendor-dashboard/", efashion_views.vendor_dashboard, name="vendor_dashboard"),
    path("vendor-profile/", efashion_views.vendor_profile_view, name="vendor_profile_view"),
    path("vendor-upload/", efashion_views.vendor_upload_product, name="vendor_upload_product"),
    path("vendor/edit-product/<int:pk>/", efashion_views.vendor_edit_product, name="vendor_edit"),
    path("vendor/delete-product/<int:pk>/", efashion_views.vendor_delete_product, name="vendor_delete"),
    path("vendor/toggle-product/<int:product_id>/", efashion_views.vendor_toggle_product, name="vendor_toggle"),

    # --- SHOPPING & CATEGORIES ---
    path("product/<int:pk>/", efashion_views.product_detail, name="product_detail"),
    path("mens-wear/", efashion_views.mens_wear, name="mens_wear"),
    path("womens-wear/", efashion_views.womens_wear, name="womens_wear"),
    path("kids-wear/", efashion_views.kids_wear, name="kids_wear"),

    # --- API ---
    path("api/new-arrivals/", efashion_views.all_new_arrivals, name="all_new_arrivals"),
]