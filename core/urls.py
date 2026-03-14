from django.urls import path
from .views import *

urlpatterns = [

    path("", signup_view, name="signup"),

    path("login/", login_view, name="login"),

    path("logout/", logout_view, name="logout"),

    path("complete-profile/", complete_profile, name="complete_profile"),

    path("vendor-dashboard/", vendor_dashboard, name="vendor_dashboard"),

    path("customer-dashboard/", customer_dashboard, name="customer_dashboard"),

]