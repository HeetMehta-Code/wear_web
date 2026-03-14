from django.contrib import admin
from .models import Admin, Vendor, Customer, Product, Cart, Order, Payment, Review

admin.site.register(Admin)
admin.site.register(Vendor)
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(Review)