# context_processors.py
from django.db import models
from .models import Cart, ShoeCategory


def cart_context(request):
    """Add cart information to all templates"""
    cart_count = 0
    cart_total = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.total_items
            cart_total = cart.total_price
        except Cart.DoesNotExist:
            pass
    else:
        # For anonymous users, get cart by session
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key, user=None)
                cart_count = cart.total_items
                cart_total = cart.total_price
            except Cart.DoesNotExist:
                pass
    
    return {
        'cart_count': cart_count,
        'cart_total': cart_total,
    }


def categories_context(request):
    """Add active categories to all templates"""
    categories = ShoeCategory.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    return {
        'categories': categories,
    }


def site_context(request):
    """Add general site information"""
    return {
        'site_name': 'Footcap',
        'site_tagline': 'Step into Style',
        'currency': 'KES',
    }