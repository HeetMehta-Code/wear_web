from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from cloudinary.models import CloudinaryField


# ==========================================
# 1. PROFILE MODELS
# ==========================================

class Admin(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Admin {self.user.email}"


class Vendor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    shopname   = models.CharField(max_length=100, null=True, blank=True)
    vendor_logo = CloudinaryField('image', folder='Vendors/logos/', null=True, blank=True)

    def __str__(self):
        return self.shopname if self.shopname else f"Vendor {self.user.email}"


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    address       = models.CharField(max_length=255, null=True, blank=True)
    profile_photo = CloudinaryField('image', folder='customers/profiles/', null=True, blank=True)

    def __str__(self):
        return self.user.email


# ==========================================
# 2. COMMERCE MODELS
# ==========================================

class Product(models.Model):

    # NEW: category choices for the dropdown
    CATEGORY_CHOICES = [
        ('mens',       "Men's Wear"),
        ('womens',     "Women's Wear"),
        ('kids',       "Kid's Wear"),
        ('bags',       'Bags'),
        ('purses',     'Purses'),
        ('belts',      'Belts'),
        ('sunglasses', 'Sun Glasses'),
        ('makeup',     'Makeup'),
        ('other',      'Other'),
    ]

    vendor   = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    name     = models.CharField(max_length=100)
    price    = models.FloatField(validators=[MinValueValidator(0.01)])

    # changed: now uses CATEGORY_CHOICES so vendor picks from list
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='other')

    stock         = models.IntegerField(validators=[MinValueValidator(0)])
    product_image = CloudinaryField('image', folder='Products/', null=True, blank=True)

    # NEW: original price to show discount (optional)
    original_price = models.FloatField(
        validators=[MinValueValidator(0.01)],
        null=True, blank=True,
        help_text="Leave blank if no discount"
    )

    # NEW: vendor can hide product without deleting it
    is_active = models.BooleanField(default=True)

    # NEW: marks product to appear in New Arrivals section
    is_new_arrival = models.BooleanField(default=True)

    # NEW: timestamp so newest products always appear first
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    # NEW: auto discount % calculation
    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.customer.user.email} - {self.product.name}"


class Order(models.Model):
    customer    = models.ForeignKey(Customer, on_delete=models.CASCADE)
    orderDate   = models.DateField(auto_now_add=True)
    status      = models.CharField(max_length=50, default="Pending")
    totalAmount = models.FloatField(validators=[MinValueValidator(0.01)])

    def __str__(self):
        return f"Order {self.id}"


class Payment(models.Model):
    order         = models.ForeignKey(Order, on_delete=models.CASCADE)
    paymentType   = models.CharField(max_length=50)
    paymentStatus = models.CharField(max_length=50)

    def __str__(self):
        return f"Payment for Order {self.order.id}"


class Review(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating   = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment  = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}"