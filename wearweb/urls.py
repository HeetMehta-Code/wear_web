from efashion import views as efashion_views
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('core.urls')),
    path("pay/<int:pk>/",       efashion_views.initiate_payment, name="initiate_payment"),
    path("payment/success/",    efashion_views.payment_success,  name="payment_success"),
    path("payment/failed/",     efashion_views.payment_failed,   name="payment_failed"),
]
