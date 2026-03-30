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
    shopname = models.CharField(max_length=100, null=True, blank=True)
    vendor_logo = CloudinaryField('image', folder='Vendors/logos/', null=True, blank=True)
    shop_address = models.TextField(null=True, blank=True)
    shop_start_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.shopname if self.shopname else f"Vendor {self.user.email}"

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, null=True, blank=True)
    profile_photo = CloudinaryField('image', folder='customers/profiles/', null=True, blank=True)

    def __str__(self):
        return self.user.email


# ==========================================
# 2. COMMERCE MODELS
# ==========================================

class Color(models.Model):
    name = models.CharField(max_length=50) # e.g., Red, Royal Blue
    code = models.CharField(max_length=7, help_text="HEX code e.g. #FF0000", null=True, blank=True)

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=20) # e.g., XL, 42, 7 (for shoes), 50ml (for makeup)
    
    def __str__(self):
        return self.name

# --- UPDATED: Main Product Model ---

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('mens', "Men's Wear"),
        ('womens', "Women's Wear"),
        ('kids', "Kid's Wear"),
        ('bags', 'Bags'),
        ('purses', 'Purses'),
        ('belts', 'Belts'),
        ('sunglasses', 'Sun Glasses'),
        ('makeup', 'Makeup'),
        ('footwear', 'Footwear'),
        ('other', 'Other'),
    ]

    SUB_CATEGORY_CHOICES = [
        ('boys', 'Boys'),
        ('girls', 'Girls'),
        ('saree', 'Sarees'),
        ('kurti', 'Kurtis'),
        ('western', 'Western'),
        ('traditional', 'Traditional'),
        ('other', 'Other'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    brand_name = models.CharField(max_length=100, default="Generic") # Added Brand Name
    description = models.TextField(null=True, blank=True)
    price = models.FloatField(validators=[MinValueValidator(0.01)])
    
    view_count = models.IntegerField(default=0)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='other')
    sub_category = models.CharField(max_length=50, choices=SUB_CATEGORY_CHOICES, default='other')

    # Total Stock (Sum of all variants)
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    product_image = CloudinaryField('image', folder='Products/', null=True, blank=True)

    original_price = models.FloatField(
        validators=[MinValueValidator(0.01)],
        null=True, blank=True,
        help_text="Leave blank if no discount"
    )

    is_active = models.BooleanField(default=True)
    is_new_arrival = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def increment_views(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def __str__(self):
        return self.name

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

# --- NEW: Product Variant Model ---

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    variant_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    image = CloudinaryField('image', folder='Products/Variants/', null=True, blank=True)
    
    def __str__(self):
        c_name = self.color.name if self.color else "No Color"
        s_name = self.size.name if self.size else "No Size"
        return f"{self.product.name} ({c_name} / {s_name})"

# ==========================================
# 3. TRANSACTIONAL MODELS
# ==========================================

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.customer.user.email} - {self.product.name}"


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    orderDate = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Pending")
    totalAmount = models.FloatField(validators=[MinValueValidator(0.01)])

    def __str__(self):
        return f"Order {self.id}"


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    paymentType = models.CharField(max_length=50)
    paymentStatus = models.CharField(max_length=50)

    def __str__(self):
        return f"Payment for Order {self.order.id}"


class Review(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}"