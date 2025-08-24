from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db import models
from django.forms import TextInput, Textarea
from .models import (
    User, County, DeliveryArea, Address, ShoeCategory, Brand, 
    ShoeSize, Color, Shoe, ShoeVariant, ShoeImage, Review, 
    ReviewImage, Wishlist, WishlistItem, Cart, CartItem, 
    Coupon, Order, OrderItem, Payment, Newsletter, 
    RecentlyViewedShoe, SiteSetting, Banner
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'date_of_birth', 'avatar', 'is_verified')
        }),
    )


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    """County Admin"""
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(DeliveryArea)
class DeliveryAreaAdmin(admin.ModelAdmin):
    """Delivery Area Admin"""
    list_display = ('name', 'county', 'shipping_fee', 'delivery_days', 'is_active')
    list_filter = ('county', 'is_active', 'delivery_days')
    search_fields = ('name', 'county__name')
    ordering = ('county__name', 'name')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Address Admin"""
    list_display = ('user', 'address_type', 'first_name', 'last_name', 'county', 'delivery_area', 'is_default')
    list_filter = ('address_type', 'county', 'is_default')
    search_fields = ('user__email', 'first_name', 'last_name', 'phone')
    raw_id_fields = ('user', 'county', 'delivery_area')


@admin.register(ShoeCategory)
class ShoeCategoryAdmin(admin.ModelAdmin):
    """Shoe Category Admin"""
    list_display = ('name', 'slug', 'is_active', 'sort_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Brand Admin"""
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(ShoeSize)
class ShoeSizeAdmin(admin.ModelAdmin):
    """Shoe Size Admin"""
    list_display = ('size', 'system', 'sort_order', 'is_active')
    list_filter = ('system', 'is_active')
    search_fields = ('size',)
    ordering = ('system', 'sort_order')


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    """Color Admin"""
    list_display = ('name', 'hex_code', 'color_preview', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'hex_code')
    ordering = ('name',)
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.hex_code
        )
    color_preview.short_description = 'Color'


class ShoeImageInline(admin.TabularInline):
    """Inline for shoe images"""
    model = ShoeImage
    extra = 1
    fields = ('image', 'color', 'alt_text', 'is_primary', 'sort_order')


class ShoeVariantInline(admin.TabularInline):
    """Inline for shoe variants"""
    model = ShoeVariant
    extra = 0
    fields = ('color', 'size', 'stock_quantity', 'price_adjustment', 'is_active')
    readonly_fields = ('sku',)


@admin.register(Shoe)
class ShoeAdmin(admin.ModelAdmin):
    """Shoe Admin"""
    list_display = ('name', 'brand', 'category', 'gender', 'base_price', 'status', 'total_stock', 'is_featured', 'created_at')
    list_filter = ('status', 'gender', 'category', 'brand', 'is_featured', 'is_new_arrival', 'is_on_sale', 'created_at')
    search_fields = ('name', 'sku', 'description', 'brand__name')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('available_sizes', 'available_colors')
    inlines = [ShoeImageInline, ShoeVariantInline]
    readonly_fields = ('view_count', 'sales_count', 'total_stock')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'brand', 'category', 'gender')
        }),
        ('Description', {
            'fields': ('short_description', 'description', 'material', 'sole_material', 'features')
        }),
        ('Pricing', {
            'fields': ('base_price', 'compare_price')
        }),
        ('Availability', {
            'fields': ('available_sizes', 'available_colors', 'status')
        }),
        ('Flags', {
            'fields': ('is_featured', 'is_new_arrival', 'is_on_sale', 'is_trending'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'sales_count', 'total_stock'),
            'classes': ('collapse',)
        }),
    )
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }


@admin.register(ShoeVariant)
class ShoeVariantAdmin(admin.ModelAdmin):
    """Shoe Variant Admin"""
    list_display = ('shoe', 'color', 'size', 'stock_quantity', 'final_price', 'is_active', 'sku')
    list_filter = ('color', 'size', 'is_active', 'shoe__brand', 'shoe__category')
    search_fields = ('shoe__name', 'sku', 'color__name', 'size__size')
    raw_id_fields = ('shoe',)
    readonly_fields = ('sku', 'final_price')
    ordering = ('shoe__name', 'color__name', 'size__sort_order')


@admin.register(ShoeImage)
class ShoeImageAdmin(admin.ModelAdmin):
    """Shoe Image Admin"""
    list_display = ('shoe', 'color', 'image_preview', 'is_primary', 'sort_order')
    list_filter = ('is_primary', 'color', 'shoe__brand')
    search_fields = ('shoe__name', 'alt_text')
    raw_id_fields = ('shoe',)
    ordering = ('shoe__name', 'sort_order')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


class ReviewImageInline(admin.TabularInline):
    """Inline for review images"""
    model = ReviewImage
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Review Admin"""
    list_display = ('shoe', 'user', 'rating', 'fit_rating', 'comfort_rating', 'is_approved', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'fit_rating', 'comfort_rating', 'is_approved', 'is_verified_purchase', 'created_at')
    search_fields = ('shoe__name', 'user__email', 'title', 'content')
    raw_id_fields = ('shoe', 'user', 'variant')
    readonly_fields = ('helpful_count',)
    inlines = [ReviewImageInline]
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = "Disapprove selected reviews"


class WishlistItemInline(admin.TabularInline):
    """Inline for wishlist items"""
    model = WishlistItem
    extra = 0
    raw_id_fields = ('shoe', 'variant')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Wishlist Admin"""
    list_display = ('user', 'name', 'is_public', 'item_count', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('user__email', 'name')
    raw_id_fields = ('user',)
    inlines = [WishlistItemInline]
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


class CartItemInline(admin.TabularInline):
    """Inline for cart items"""
    model = CartItem
    extra = 0
    raw_id_fields = ('shoe', 'variant')
    readonly_fields = ('unit_price', 'total_price')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Cart Admin"""
    list_display = ('id', 'user', 'total_items', 'total_price', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'session_key')
    raw_id_fields = ('user',)
    inlines = [CartItemInline]
    readonly_fields = ('total_items', 'total_price')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Coupon Admin"""
    list_display = ('code', 'discount_type', 'discount_value', 'usage_status', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')
    readonly_fields = ('used_count',)
    
    def usage_status(self, obj):
        if obj.usage_limit:
            return f"{obj.used_count}/{obj.usage_limit}"
        return f"{obj.used_count}/∞"
    usage_status.short_description = 'Usage'


class OrderItemInline(admin.TabularInline):
    """Inline for order items"""
    model = OrderItem
    extra = 0
    raw_id_fields = ('shoe', 'variant')
    readonly_fields = ('total_price',)


class PaymentInline(admin.TabularInline):
    """Inline for payments"""
    model = Payment
    extra = 0
    readonly_fields = ('checkout_request_id', 'mpesa_receipt', 'status', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order Admin"""
    list_display = ('order_number', 'user', 'status', 'total_amount', 'payment_status', 'created_at', 'shipped_at', 'delivered_at')
    list_filter = ('status', 'payment_status', 'created_at', 'shipped_at', 'delivered_at')
    search_fields = ('order_number', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user', 'coupon')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline, PaymentInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'coupon')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_amount', 'discount_amount', 'total_amount')
        }),
        ('Addresses', {
            'fields': ('shipping_address', 'billing_address')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark selected orders as processing"
    
    def mark_as_shipped(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='shipped', shipped_at=timezone.now())
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='delivered', delivered_at=timezone.now())
    mark_as_delivered.short_description = "Mark selected orders as delivered"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment Admin"""
    list_display = ('checkout_request_id', 'order', 'phone_number', 'amount', 'status', 'mpesa_receipt', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('checkout_request_id', 'mpesa_receipt', 'phone_number', 'order__order_number')
    raw_id_fields = ('order',)
    readonly_fields = ('checkout_request_id', 'mpesa_receipt', 'raw_response', 'created_at', 'updated_at')


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Newsletter Admin"""
    list_display = ('email', 'is_active', 'subscribed_at', 'unsubscribed_at')
    list_filter = ('is_active', 'subscribed_at', 'unsubscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at', 'unsubscribed_at')
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        queryset.update(is_active=True, unsubscribed_at=None)
    activate_subscriptions.short_description = "Activate selected subscriptions"
    
    def deactivate_subscriptions(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_active=False, unsubscribed_at=timezone.now())
    deactivate_subscriptions.short_description = "Deactivate selected subscriptions"


@admin.register(RecentlyViewedShoe)
class RecentlyViewedShoeAdmin(admin.ModelAdmin):
    """Recently Viewed Shoe Admin"""
    list_display = ('user', 'shoe', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('user__email', 'shoe__name')
    raw_id_fields = ('user', 'shoe')
    readonly_fields = ('viewed_at',)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """Site Setting Admin"""
    list_display = ('key', 'value_preview', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Banner Admin"""
    list_display = ('title', 'image_preview', 'is_active', 'sort_order', 'valid_from', 'valid_to')
    list_filter = ('is_active', 'valid_from', 'valid_to', 'created_at')
    search_fields = ('title', 'subtitle', 'link_text')
    readonly_fields = ('created_at',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


# Admin site customization
admin.site.site_header = "Footwear Store Admin"
admin.site.site_title = "Footwear Admin"
admin.site.index_title = "Welcome to Footwear Store Administration"