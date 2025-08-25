# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, Avg, F
from django.core.paginator import Paginator
from django.utils import timezone
from .models import (
    Shoe, ShoeCategory, Brand, ShoeVariant, Color, ShoeSize, 
    ShoeImage, Cart, CartItem, Banner, Review, RecentlyViewedShoe
)
import json

def home(request):
    """Home page view with featured products and collections"""
    # Get active banners
    banners = Banner.objects.filter(is_active=True).order_by('sort_order')[:3]
    
    # Get featured products
    featured_shoes = Shoe.objects.filter(
        is_featured=True, 
        status='active'
    ).select_related('brand', 'category').prefetch_related(
        'images', 'variants__color', 'variants__size'
    )[:8]
    
    # Get new arrivals
    new_arrivals = Shoe.objects.filter(
        is_new_arrival=True,
        status='active'
    ).select_related('brand', 'category').prefetch_related(
        'images', 'variants__color', 'variants__size'
    )[:8]
    
    # Get trending products
    trending_shoes = Shoe.objects.filter(
        is_trending=True,
        status='active'
    ).select_related('brand', 'category').prefetch_related(
        'images', 'variants__color', 'variants__size'
    )[:4]
    
    # Get categories for collections
    categories = ShoeCategory.objects.filter(is_active=True)[:3]
    
    # Get popular brands
    brands = Brand.objects.filter(is_active=True)[:6]
    
    context = {
        'banners': banners,
        'featured_shoes': featured_shoes,
        'new_arrivals': new_arrivals,
        'trending_shoes': trending_shoes,
        'categories': categories,
        'brands': brands,
    }
    
    return render(request, 'home.html', context)

def product_detail(request, slug):
    """Product detail view with size/color selection"""
    shoe = get_object_or_404(
        Shoe.objects.select_related('brand', 'category').prefetch_related(
            'images__color',
            'variants__color',
            'variants__size',
            'available_colors',
            'available_sizes'
        ),
        slug=slug,
        status='active'
    )
    
    # Get all variants for this shoe
    variants = ShoeVariant.objects.filter(
        shoe=shoe,
        is_active=True,
        stock_quantity__gt=0
    ).select_related('color', 'size')
    
    # Get available colors (only those with stock)
    available_colors = Color.objects.filter(
        id__in=variants.values_list('color_id', flat=True)
    ).distinct()
    
    # Get available sizes (only those with stock)
    available_sizes = ShoeSize.objects.filter(
        id__in=variants.values_list('size_id', flat=True)
    ).distinct().order_by('sort_order')
    
    # Get product images
    images = ShoeImage.objects.filter(shoe=shoe).order_by('sort_order')
    
    # Get reviews
    reviews = Review.objects.filter(
        shoe=shoe,
        is_approved=True
    ).select_related('user').order_by('-created_at')[:10]
    
    # Get related products
    related_shoes = Shoe.objects.filter(
        category=shoe.category,
        status='active'
    ).exclude(id=shoe.id).select_related(
        'brand', 'category'
    ).prefetch_related('images')[:4]
    
    # Track recently viewed (for authenticated users)
    if request.user.is_authenticated:
        RecentlyViewedShoe.objects.update_or_create(
            user=request.user,
            shoe=shoe,
            defaults={'viewed_at': timezone.now()}
        )
    
    # Increment view count
    Shoe.objects.filter(id=shoe.id).update(view_count=F('view_count') + 1)
    
    context = {
        'shoe': shoe,
        'variants': variants,
        'available_colors': available_colors,
        'available_sizes': available_sizes,
        'images': images,
        'reviews': reviews,
        'related_shoes': related_shoes,
        'variants_json': json.dumps({
            f"{v.color_id}-{v.size_id}": {
                'id': v.id,
                'stock': v.stock_quantity,
                'price': str(v.final_price),
                'sku': v.sku
            } for v in variants
        })
    }
    
    return render(request, 'product_detail.html', context)

def get_variant_info(request):
    """AJAX view to get variant information"""
    if request.method == 'GET':
        color_id = request.GET.get('color_id')
        size_id = request.GET.get('size_id')
        shoe_id = request.GET.get('shoe_id')
        
        try:
            variant = ShoeVariant.objects.get(
                shoe_id=shoe_id,
                color_id=color_id,
                size_id=size_id,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'variant_id': variant.id,
                'stock': variant.stock_quantity,
                'price': str(variant.final_price),
                'sku': variant.sku,
                'in_stock': variant.is_in_stock
            })
        except ShoeVariant.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'This size and color combination is not available'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@require_POST
def add_to_cart(request):
    """Add item to cart"""
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            variant = get_object_or_404(ShoeVariant, id=variant_id, is_active=True)
            
            # Check stock
            if variant.stock_quantity < quantity:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'Only {variant.stock_quantity} items in stock'
                    })
                else:
                    messages.error(request, f'Only {variant.stock_quantity} items in stock')
                    return redirect('product_detail', slug=variant.shoe.slug)
            
            # Get or create cart
            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                # For anonymous users, use session
                cart_id = request.session.get('cart_id')
                if cart_id:
                    try:
                        cart = Cart.objects.get(id=cart_id, user=None)
                    except Cart.DoesNotExist:
                        cart = Cart.objects.create(session_key=request.session.session_key)
                        request.session['cart_id'] = cart.id
                else:
                    cart = Cart.objects.create(session_key=request.session.session_key)
                    request.session['cart_id'] = cart.id
            
            # Add or update cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                variant=variant,
                defaults={'shoe': variant.shoe, 'quantity': quantity}
            )
            
            if not created:
                # Update quantity if item already exists
                new_quantity = cart_item.quantity + quantity
                if new_quantity > variant.stock_quantity:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': f'Cannot add more items. Only {variant.stock_quantity} available'
                        })
                    else:
                        messages.error(request, f'Cannot add more items. Only {variant.stock_quantity} available')
                        return redirect('product_detail', slug=variant.shoe.slug)
                
                cart_item.quantity = new_quantity
                cart_item.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Item added to cart successfully',
                    'cart_count': cart.total_items,
                    'cart_total': str(cart.total_price)
                })
            else:
                messages.success(request, 'Item added to cart successfully')
                return redirect('product_detail', slug=variant.shoe.slug)
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred while adding item to cart'
                })
            else:
                messages.error(request, 'An error occurred while adding item to cart')
                return redirect('product_detail', slug=variant.shoe.slug)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Min, Max
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json

from .models import (
    Shoe, ShoeCategory, Brand, Color, ShoeSize, Cart, CartItem, 
    ShoeVariant, County, DeliveryArea
)
def product_list(request):
    """Product list with filtering, search and pagination"""
    shoes = Shoe.objects.filter(status='active').select_related(
        'brand', 'category'
    ).prefetch_related(
        'images', 'variants', 'available_colors', 'available_sizes'
    )
    
    # Get all filter options
    categories = ShoeCategory.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    colors = Color.objects.filter(is_active=True)
    sizes = ShoeSize.objects.filter(is_active=True).order_by('sort_order')
    
    # Get price range
    price_range = shoes.aggregate(
        min_price=Min('base_price'),
        max_price=Max('base_price')
    )
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        shoes = shoes.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__name__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(material__icontains=search_query)
        )
    
    # Category filter
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(ShoeCategory, slug=category_slug)
        shoes = shoes.filter(category=selected_category)
    
    # Brand filter
    brand_slug = request.GET.get('brand')
    selected_brand = None
    if brand_slug:
        selected_brand = get_object_or_404(Brand, slug=brand_slug)
        shoes = shoes.filter(brand=selected_brand)
    
    # Gender filter
    gender = request.GET.get('gender')
    if gender:
        shoes = shoes.filter(gender=gender)
    
    # Color filter
    color_id = request.GET.get('color')
    selected_color = None
    if color_id:
        selected_color = get_object_or_404(Color, id=color_id)
        shoes = shoes.filter(available_colors=selected_color)
    
    # Size filter
    size_id = request.GET.get('size')
    selected_size = None
    if size_id:
        selected_size = get_object_or_404(ShoeSize, id=size_id)
        shoes = shoes.filter(available_sizes=selected_size)
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        shoes = shoes.filter(base_price__gte=min_price)
    if max_price:
        shoes = shoes.filter(base_price__lte=max_price)
    
    # Special filters
    if request.GET.get('featured'):
        shoes = shoes.filter(is_featured=True)
    if request.GET.get('new_arrival'):
        shoes = shoes.filter(is_new_arrival=True)
    if request.GET.get('on_sale'):
        shoes = shoes.filter(is_on_sale=True)
    if request.GET.get('in_stock'):
        shoes = shoes.filter(variants__stock_quantity__gt=0).distinct()
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        shoes = shoes.order_by('base_price')
    elif sort_by == 'price_high':
        shoes = shoes.order_by('-base_price')
    elif sort_by == 'name_asc':
        shoes = shoes.order_by('name')
    elif sort_by == 'name_desc':
        shoes = shoes.order_by('-name')
    elif sort_by == 'popular':
        shoes = shoes.order_by('-sales_count', '-view_count')
    elif sort_by == 'rating':
        shoes = shoes.order_by('-sales_count')  # You can implement proper rating sorting
    else:  # newest
        shoes = shoes.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(shoes, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'shoes': page_obj,
        'categories': categories,
        'brands': brands,
        'colors': colors,
        'sizes': sizes,
        'price_range': price_range,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'selected_color': selected_color,
        'selected_size': selected_size,
        'search_query': search_query,
        'current_filters': {
            'category': category_slug,
            'brand': brand_slug,
            'gender': gender,
            'color': color_id,
            'size': size_id,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort_by,
            'search': search_query,
        },
        'total_products': paginator.count,
    }
    
    return render(request, 'products.html', context)

def category_detail(request, slug):
    """Category detail view showing products in specific category"""
    category = get_object_or_404(ShoeCategory, slug=slug, is_active=True)
    
    shoes = Shoe.objects.filter(
        category=category, 
        status='active'
    ).select_related('brand').prefetch_related('images', 'variants')
    
    # Apply additional filters if any
    brands = Brand.objects.filter(shoes__category=category, is_active=True).distinct()
    
    # Brand filter
    brand_slug = request.GET.get('brand')
    selected_brand = None
    if brand_slug:
        selected_brand = get_object_or_404(Brand, slug=brand_slug)
        shoes = shoes.filter(brand=selected_brand)
    
    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        shoes = shoes.filter(base_price__gte=min_price)
    if max_price:
        shoes = shoes.filter(base_price__lte=max_price)
    
    # Gender filter
    gender = request.GET.get('gender')
    if gender:
        shoes = shoes.filter(gender=gender)
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        shoes = shoes.order_by('base_price')
    elif sort_by == 'price_high':
        shoes = shoes.order_by('-base_price')
    elif sort_by == 'name_asc':
        shoes = shoes.order_by('name')
    elif sort_by == 'popular':
        shoes = shoes.order_by('-sales_count', '-view_count')
    else:
        shoes = shoes.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(shoes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get price range for this category
    price_range = shoes.aggregate(
        min_price=Min('base_price'),
        max_price=Max('base_price')
    )
    
    context = {
        'category': category,
        'shoes': page_obj,
        'brands': brands,
        'selected_brand': selected_brand,
        'price_range': price_range,
        'current_filters': {
            'brand': brand_slug,
            'gender': gender,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort_by,
        },
        'total_products': paginator.count,
    }
    
    return render(request, 'category-detail.html', context)


def cart_summary(request):
    """Cart summary view"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related(
        'shoe', 'variant__color', 'variant__size', 'shoe__brand'
    ).prefetch_related('shoe__images')
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    
    # Get shipping options based on user location or default
    shipping_fee = 0
    delivery_areas = DeliveryArea.objects.filter(is_active=True).select_related('county')
    
    if request.user.is_authenticated:
        # Try to get user's default shipping address
        default_address = request.user.addresses.filter(
            address_type='shipping', 
            is_default=True
        ).first()
        if default_address and default_address.delivery_area:
            shipping_fee = default_address.shipping_fee
    
    total = subtotal + shipping_fee
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total': total,
        'delivery_areas': delivery_areas,
    }
    
    return render(request, 'cart-summary.html', context)



@require_POST
def update_cart_item(request):
    """Update cart item quantity via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity', 1))
            
            cart = get_or_create_cart(request)
            cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
            
            if quantity <= 0:
                cart_item.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Item removed from cart',
                    'cart_count': cart.total_items,
                    'cart_total': cart.total_price,
                    'item_removed': True
                })
            
            if quantity > cart_item.variant.stock_quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {cart_item.variant.stock_quantity} items available'
                })
            
            cart_item.quantity = quantity
            cart_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cart updated successfully',
                'cart_count': cart.total_items,
                'cart_total': cart.total_price,
                'item_total': cart_item.total_price,
                'subtotal': sum(item.total_price for item in cart.items.all())
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while updating cart'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@require_POST
def remove_cart_item(request):
    """Remove item from cart via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            cart = get_or_create_cart(request)
            cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
            cart_item.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': cart.total_items,
                'cart_total': cart.total_price,
                'subtotal': sum(item.total_price for item in cart.items.all())
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while removing item'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@require_POST
def clear_cart(request):
    """Clear entire cart via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            cart = get_or_create_cart(request)
            cart.items.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Cart cleared successfully',
                'cart_count': 0,
                'cart_total': 0
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while clearing cart'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'session_key': None}
        )
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(
            session_key=session_key,
            user=None
        )
    
    return cart


def get_cart_variants_json(shoe):
    """Get variants data as JSON for JavaScript"""
    variants = {}
    for variant in shoe.variants.all():
        key = f"{variant.color.id}-{variant.size.id}"
        variants[key] = {
            'id': variant.id,
            'price': str(variant.final_price),
            'stock': variant.stock_quantity,
            'sku': variant.sku
        }
    return json.dumps(variants)