# efashion/urls.py

from django.urls import path
from django.contrib import admin
from efashion import views as efashion_views 

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- AUTH ---
    path("", efashion_views.signup_view, name="signup"),
    path("login/", efashion_views.login_view, name="login"),
    path("logout/", efashion_views.logout_view, name="logout"),
    # --- VENDOR MANAGEMENT ---
    path("vendor-dashboard/", efashion_views.vendor_dashboard, name="vendor_dashboard"),
    path("vendor-profile/", efashion_views.vendor_profile_view, name="vendor_profile_view"),
    path("vendor-upload/", efashion_views.vendor_upload_product, name="vendor_upload_product"),
    path("vendor/edit-product/<int:pk>/", efashion_views.vendor_edit_product, name="vendor_edit"),
    path("vendor/delete-product/<int:pk>/", efashion_views.vendor_delete_product, name="vendor_delete"),
    path("vendor/toggle-product/<int:product_id>/", efashion_views.vendor_toggle_product, name="vendor_toggle"),
    # --- CUSTOMER FLOW ---
    path("customer-dashboard/", efashion_views.customer_dashboard, name="customer_dashboard"),
    # ENSURE THIS NAME IS EXACTLY 'customer_profile'
    path("customer-profile/", efashion_views.customer_profile, name="customer_profile"),
    
    # NAVIGATION & SEARCH (Use efashion_views prefix to stay consistent)
    path('search/', efashion_views.search_view, name='search_products'),
    path('brand/<str:brand_name>/', efashion_views.brand_product_view, name='brand_products'),
    path('collection/<str:feature_type>/', efashion_views.feature_collection_view, name='feature_collection'),
    path('about/', efashion_views.about_us, name='about_us'),
    path('contact/', efashion_views.contact_us, name='contact_us'),
    path("api/new-arrivals/", efashion_views.all_new_arrivals, name="all_new_arrivals"),
    path('shop/<str:cat_slug>/', efashion_views.category_view, name='category_view'),
    path('shop/<str:cat_slug>/<str:sub_slug>/', efashion_views.category_view, name='sub_category_view'),
    # --- SHOPPING ---
    path("mens-wear/", efashion_views.mens_wear, name="mens_wear"),
    path("womens-wear/", efashion_views.womens_wear, name="womens_wear"),
    path("kids-wear/", efashion_views.kids_wear, name="kids_wear"),
    # In efashion/urls.py
    path("product/<int:pk>/", efashion_views.product_detail, name="product_detail"),
]