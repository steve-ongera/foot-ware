from django.urls import path
from . import views


urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Products
    path('products/', views.product_list, name='products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('ajax/get-variant-info/', views.get_variant_info, name='get_variant_info'),
    path('ajax/add-to-cart/', views.add_to_cart, name='add_to_cart'),

    # Category details (with slug)
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    
    # Cart views
    path("cart/", views.cart_summary, name="cart_summary"),
    path("cart/update/", views.update_cart_item, name="update_cart_item"),
    path("cart/remove/", views.remove_cart_item, name="remove_cart_item"),
    path("cart/clear/", views.clear_cart, name="clear_cart"),
]