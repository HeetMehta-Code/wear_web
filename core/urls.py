from django.urls import path
from .views import signup_view,login_view
from core import views

urlpatterns=[
    path('signup/',signup_view,name='signup'),
    path('login/',login_view,name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
]