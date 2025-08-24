from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from PIL import Image
import os
import random
import string


class User(AbstractUser):
    """Extended User model"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class County(models.Model):
    """Kenyan Counties"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Counties'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DeliveryArea(models.Model):
    """Delivery areas within counties with shipping fees"""
    name = models.CharField(max_length=100)
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='delivery_areas')
    shipping_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    delivery_days = models.IntegerField(default=1)  # Expected delivery days
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'county']
        ordering = ['county__name', 'name']
    
    def __str__(self):
        return f"{self.name}, {self.county.name}"


class Address(models.Model):
    """User addresses for shipping and billing"""
    ADDRESS_TYPES = (
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Address fields
    county = models.ForeignKey(County, on_delete=models.CASCADE, blank=True, null=True)
    delivery_area = models.ForeignKey(DeliveryArea, on_delete=models.CASCADE, blank=True, null=True)
    detailed_address = models.TextField(help_text="Building name, floor, apartment number, landmark, etc.", blank=True, null=True)

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.delivery_area.name if self.delivery_area else ''}, {self.county.name if self.county else ''}"
    
    @property
    def shipping_fee(self):
        return self.delivery_area.shipping_fee if self.delivery_area else 0
    
    @property
    def full_address(self):
        return f"{self.detailed_address}, {self.delivery_area.name if self.delivery_area else ''}, {self.county.name if self.county else ''}, Kenya"

    def save(self, *args, **kwargs):
        # Ensure only one default address per type per user
        if self.is_default:
            Address.objects.filter(
                user=self.user, 
                address_type=self.address_type, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ShoeCategory(models.Model):
    """Shoe categories (e.g., Sneakers, Formal, Boots, Sandals)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Shoe Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shoe_category_detail', kwargs={'slug': self.slug})


class Brand(models.Model):
    """Shoe brands (Nike, Adidas, Puma, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/', null=True, blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ShoeSize(models.Model):
    """Available shoe sizes"""
    SIZE_SYSTEMS = (
        ('US', 'US Size'),
        ('UK', 'UK Size'),
        ('EU', 'EU Size'),
    )
    
    size = models.CharField(max_length=10)  # e.g., "9", "9.5", "42"
    system = models.CharField(max_length=5, choices=SIZE_SYSTEMS, default='US')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['size', 'system']
        ordering = ['system', 'sort_order', 'size']
    
    def __str__(self):
        return f"{self.size} ({self.system})"


class Color(models.Model):
    """Available shoe colors"""
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, help_text="Hex color code (e.g., #FF0000)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Shoe(models.Model):
    """Main shoe model"""
    SHOE_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
    )
    
    GENDER_CHOICES = (
        ('men', 'Men'),
        ('women', 'Women'),
        ('unisex', 'Unisex'),
        ('kids', 'Kids'),
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.TextField(max_length=500, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    
    # Shoe specific fields
    category = models.ForeignKey(ShoeCategory, on_delete=models.CASCADE, related_name='shoes')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='shoes')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # Available sizes and colors (many-to-many for flexibility)
    available_sizes = models.ManyToManyField(ShoeSize, related_name='shoes')
    available_colors = models.ManyToManyField(Color, related_name='shoes')
    
    # Base pricing (can be overridden by variants)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Materials and features
    material = models.CharField(max_length=100, blank=True, help_text="e.g., Leather, Canvas, Synthetic")
    sole_material = models.CharField(max_length=100, blank=True)
    features = models.TextField(blank=True, help_text="Special features like waterproof, breathable, etc.")
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    
    # Status and flags
    status = models.CharField(max_length=20, choices=SHOE_STATUS, default='active')
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_on_sale = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    sales_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand.name} {self.name}" if self.brand else self.name

    def get_absolute_url(self):
        return reverse('shoe_detail', kwargs={'slug': self.slug})

    @property
    def discount_percentage(self):
        if self.compare_price and self.base_price < self.compare_price:
            return int(((self.compare_price - self.base_price) / self.compare_price) * 100)
        return 0

    @property
    def total_stock(self):
        """Total stock across all variants"""
        return sum(variant.stock_quantity for variant in self.variants.all())

    @property
    def is_in_stock(self):
        return self.total_stock > 0

    @property
    def available_size_range(self):
        """Get min and max available sizes"""
        sizes = self.available_sizes.all().order_by('sort_order')
        if sizes:
            return f"{sizes.first().size} - {sizes.last().size}"
        return "N/A"

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
        return 0

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()


class ShoeVariant(models.Model):
    """Specific shoe variants (color + size combinations)"""
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(ShoeSize, on_delete=models.CASCADE)
    
    # Variant specific details
    sku = models.CharField(max_length=50, unique=True)
    stock_quantity = models.IntegerField(default=0)
    price_adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Price difference from base price (can be negative)"
    )
    
    # Optional variant-specific image
    image = models.ImageField(upload_to='shoe_variants/', null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['shoe', 'color', 'size']
        ordering = ['color__name', 'size__sort_order']

    def __str__(self):
        return f"{self.shoe.name} - {self.color.name} - Size {self.size.size}"

    @property
    def final_price(self):
        """Calculate final price including any adjustments"""
        return self.shoe.base_price + self.price_adjustment

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    def save(self, *args, **kwargs):
        if not self.sku:
            # Generate SKU: BRAND_SHOE_COLOR_SIZE
            brand_code = self.shoe.brand.name[:3].upper() if self.shoe.brand else 'SHO'
            shoe_code = self.shoe.name[:3].upper()
            color_code = self.color.name[:3].upper()
            size_code = str(self.size.size).replace('.', '_')
            self.sku = f"{brand_code}_{shoe_code}_{color_code}_{size_code}"
        super().save(*args, **kwargs)


class ShoeImage(models.Model):
    """Shoe images"""
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE, related_name='images')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True, 
                             help_text="If specified, this image is for a specific color")
    image = models.ImageField(upload_to='shoes/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        color_info = f" - {self.color.name}" if self.color else ""
        return f"{self.shoe.name}{color_info} - Image {self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Resize image if needed
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                img.thumbnail((800, 800))
                img.save(self.image.path)


class Review(models.Model):
    """Shoe reviews"""
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(ShoeVariant, on_delete=models.CASCADE, null=True, blank=True,
                               help_text="Specific variant reviewed")
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Shoe-specific review fields
    fit_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True,
                                   help_text="How well does it fit? (1=Too small, 5=Perfect)")
    comfort_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    quality_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    
    is_approved = models.BooleanField(default=False)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['shoe', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.shoe.name} - {self.rating} stars by {self.user.email}"


class ReviewImage(models.Model):
    """Images attached to reviews"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review image for {self.review.shoe.name}"


class Wishlist(models.Model):
    """User wishlist"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    name = models.CharField(max_length=100, default='My Wishlist')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.name}"


class WishlistItem(models.Model):
    """Items in wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE)
    variant = models.ForeignKey(ShoeVariant, on_delete=models.CASCADE, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['wishlist', 'shoe', 'variant']

    def __str__(self):
        return f"{self.wishlist.name} - {self.shoe.name}"


class Cart(models.Model):
    """Shopping cart"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id} - {self.user.email if self.user else 'Anonymous'}"

    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    """Items in shopping cart - always linked to specific shoe variant"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE)
    variant = models.ForeignKey(ShoeVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'variant']

    def __str__(self):
        return f"{self.shoe.name} - {self.variant.color.name} - Size {self.variant.size.size} x {self.quantity}"

    @property
    def unit_price(self):
        return self.variant.final_price

    @property
    def total_price(self):
        return self.unit_price * self.quantity


class Coupon(models.Model):
    """Discount coupons"""
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return (self.is_active and 
                self.valid_from <= now <= self.valid_to and
                (self.usage_limit is None or self.used_count < self.usage_limit))


class Order(models.Model):
    """Customer orders"""
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Addresses
    shipping_address = models.TextField()
    billing_address = models.TextField()
    
    # Payment
    payment_method = models.CharField(max_length=50, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    
    # Coupon
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate a random 9-character alphanumeric string
            self.order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE)
    variant = models.ForeignKey(ShoeVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.shoe.name} - {self.variant.color.name} - Size {self.variant.size.size}"


class Payment(models.Model):
    """Track payments for orders - M-Pesa integration"""
    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    checkout_request_id = models.CharField(max_length=100, unique=True)  # From Safaricom STK push response
    mpesa_receipt = models.CharField(max_length=100, null=True, blank=True)  # Returned after success
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    transaction_date = models.CharField(max_length=20, null=True, blank=True)  # keep raw string first
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="PENDING")
    raw_response = models.JSONField(null=True, blank=True)  # store full Safaricom callback for auditing

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.checkout_request_id} - {self.status}"


class Newsletter(models.Model):
    """Newsletter subscriptions"""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email


class RecentlyViewedShoe(models.Model):
    """Recently viewed shoes by user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed_shoes')
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'shoe']
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.email} viewed {self.shoe.name}"


class SiteSetting(models.Model):
    """Site configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class Banner(models.Model):
    """Homepage banners and promotional content"""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='banners/')
    mobile_image = models.ImageField(upload_to='banners/mobile/', null=True, blank=True)
    link_url = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title