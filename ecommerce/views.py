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

def products(request):
    """Products listing page with filters"""
    shoes = Shoe.objects.filter(status='active').select_related(
        'brand', 'category'
    ).prefetch_related('images')
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        shoes = shoes.filter(category__slug=category_slug)
    
    # Filter by brand
    brand_slug = request.GET.get('brand')
    if brand_slug:
        shoes = shoes.filter(brand__slug=brand_slug)
    
    # Filter by gender
    gender = request.GET.get('gender')
    if gender:
        shoes = shoes.filter(gender=gender)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        shoes = shoes.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__name__icontains=search_query)
        )
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        shoes = shoes.filter(base_price__gte=min_price)
    if max_price:
        shoes = shoes.filter(base_price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        shoes = shoes.order_by('base_price')
    elif sort_by == 'price_high':
        shoes = shoes.order_by('-base_price')
    elif sort_by == 'newest':
        shoes = shoes.order_by('-created_at')
    elif sort_by == 'popular':
        shoes = shoes.order_by('-view_count')
    else:
        shoes = shoes.order_by('name')
    
    # Pagination
    paginator = Paginator(shoes, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = ShoeCategory.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'brands': brands,
        'current_category': category_slug,
        'current_brand': brand_slug,
        'current_gender': gender,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    
    return render(request, 'products.html', context)