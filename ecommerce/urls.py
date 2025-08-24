from django.urls import path
from . import views


urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Products
    path('products/', views.products, name='products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # AJAX endpoints
    path('ajax/get-variant-info/', views.get_variant_info, name='get_variant_info'),
    path('ajax/add-to-cart/', views.add_to_cart, name='add_to_cart'),
]