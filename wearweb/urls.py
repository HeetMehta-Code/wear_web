from efashion import views as efashion_views
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('core.urls')),
    path("pay/cart/",          efashion_views.initiate_cart_payment, name="initiate_cart_payment"),
    path("pay/<int:pk>/",       efashion_views.initiate_payment, name="initiate_payment"),
    path("payment/success/",    efashion_views.payment_success,  name="payment_success"),
    path("payment/failed/",     efashion_views.payment_failed,   name="payment_failed"),
    path("dummy-pay/<int:order_id>/", efashion_views.dummy_payment, name="dummy_payment"),
    path('admin-panel/', efashion_views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/vendors/', efashion_views.admin_vendors, name='admin_vendors'),
    path('admin-panel/vendors/toggle/<int:pk>/', efashion_views.admin_toggle_vendor,  name='admin_toggle_vendor'),
    path('admin-panel/vendors/delete/<int:pk>/', efashion_views.admin_delete_vendor,  name='admin_delete_vendor'),
    path('admin-panel/customers/', efashion_views.admin_customers, name='admin_customers'),
    path('admin-panel/customers/toggle/<int:pk>/', efashion_views.admin_toggle_customer, name='admin_toggle_customer'),
    path('admin-panel/products/', efashion_views.admin_products, name='admin_products'),
    path('admin-panel/products/toggle/<int:pk>/', efashion_views.admin_toggle_product, name='admin_toggle_product'),
    path('admin-panel/products/delete/<int:pk>/', efashion_views.admin_delete_product, name='admin_delete_product'),
    path('admin-panel/orders/', efashion_views.admin_orders, name='admin_orders'),
    path('admin-panel/orders/status/<int:pk>/', efashion_views.admin_update_order_status, name='admin_update_order_status'),
    path('admin-panel/orders/delete/<int:pk>/', efashion_views.admin_delete_order, name='admin_delete_order'),
    path('admin-panel/finance/', efashion_views.admin_finance, name='admin_finance'),
    path('admin-panel/messages/', efashion_views.admin_messages, name='admin_messages'),
    path('admin-panel/reviews/', efashion_views.admin_reviews, name='admin_reviews'),
    path('admin-panel/reviews/delete/<int:pk>/', efashion_views.admin_delete_review,  name='admin_delete_review'),
]
