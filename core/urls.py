from django.urls import path
from .views import (
    signup_view,
    login_view,
    logout_view,
    complete_profile,
    customer_dashboard,
    customer_profile,
    vendor_dashboard,
    all_new_arrivals,
    vendor_upload_product,
    vendor_toggle_product,
)

urlpatterns = [
    path("", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("complete-profile/", complete_profile, name="complete_profile"),
    path("vendor-dashboard/", vendor_dashboard, name="vendor_dashboard"),
    path("customer-dashboard/", customer_dashboard, name="customer_dashboard"),
    path("api/new-arrivals/", all_new_arrivals, name="all_new_arrivals"),
    path("vendor/upload/", vendor_upload_product, name="vendor_upload"),
    path("vendor/toggle/<int:product_id>/", vendor_toggle_product, name="vendor_toggle"),
    path("customer-profile/", customer_profile, name="customer_profile"),
]