# Footwear E-commerce Platform

A comprehensive Django-based e-commerce platform specifically designed for selling footwear online, with built-in support for Kenyan counties and M-Pesa payment integration.

## 🚀 Features

### Core E-commerce Features
- **Product Management**: Complete shoe catalog with brands, categories, sizes, and colors
- **Variant System**: Support for different color and size combinations with individual pricing
- **Shopping Cart**: Session-based cart for anonymous users and persistent cart for registered users
- **Wishlist**: Multiple wishlist support with public/private options
- **Order Management**: Complete order lifecycle from cart to delivery
- **User Reviews**: Product reviews with ratings for fit, comfort, and quality
- **Coupon System**: Percentage and fixed amount discount coupons

### Kenyan Market Features
- **County-based Delivery**: Support for all Kenyan counties with specific delivery areas
- **Dynamic Shipping Fees**: Area-specific shipping costs and delivery timeframes
- **M-Pesa Integration**: Mobile money payment processing via Safaricom M-Pesa STK Push

### User Management
- **Extended User Model**: Custom user model with email authentication
- **Multiple Addresses**: Separate billing and shipping addresses per user
- **User Verification**: Email verification system
- **Recent Views**: Track recently viewed products

### SEO & Marketing
- **SEO Optimization**: Meta tags, slugs, and SEO-friendly URLs
- **Newsletter**: Email subscription management
- **Banners**: Dynamic homepage banners and promotional content
- **Analytics**: View counts and sales tracking

## 📊 Database Models Overview

### User & Address Models
- `User`: Extended Django user model with email authentication
- `County`: Kenyan counties management
- `DeliveryArea`: Delivery zones within counties with shipping fees
- `Address`: User shipping and billing addresses

### Product Models
- `Shoe`: Main product model with comprehensive shoe attributes
- `ShoeCategory`: Product categories (Sneakers, Formal, Boots, etc.)
- `Brand`: Shoe brands (Nike, Adidas, Puma, etc.)
- `ShoeSize`: Available sizes with different sizing systems (US, UK, EU)
- `Color`: Available colors with hex codes
- `ShoeVariant`: Specific combinations of shoe, color, and size
- `ShoeImage`: Product images with color-specific support

### E-commerce Models
- `Cart` & `CartItem`: Shopping cart functionality
- `Order` & `OrderItem`: Order management
- `Payment`: M-Pesa payment tracking
- `Coupon`: Discount coupon system

### User Interaction Models
- `Review` & `ReviewImage`: Product reviews with images
- `Wishlist` & `WishlistItem`: User wishlists
- `RecentlyViewedShoe`: Recently viewed products

### CMS Models
- `Banner`: Homepage promotional banners
- `Newsletter`: Email subscriptions
- `SiteSetting`: Site configuration

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Django 4.0+
- PostgreSQL (recommended) or SQLite for development
- Redis (for session management and caching)
- Pillow (for image processing)

### Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd footwear-ecommerce
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file with the following variables:
```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/footwear_db

# M-Pesa Configuration
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=your-shortcode
MPESA_PASSKEY=your-passkey
MPESA_CALLBACK_URL=https://yourdomain.com/mpesa/callback/

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

5. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create Superuser**
```bash
python manage.py createsuperuser
```

7. **Load Initial Data** (optional)
```bash
python manage.py loaddata counties.json  # Load Kenyan counties
python manage.py loaddata shoe_sizes.json  # Load common shoe sizes
```

8. **Run Development Server**
```bash
python manage.py runserver
```

## 📋 Required Dependencies

Add these to your `requirements.txt`:

```txt
Django>=4.0
Pillow>=9.0
psycopg2-binary>=2.9
django-environ>=0.9
requests>=2.28  # For M-Pesa API calls
django-cors-headers>=3.13  # If building API
djangorestframework>=3.14  # If building API
celery>=5.2  # For background tasks
redis>=4.3  # For caching and sessions
```

## 🏗️ Project Structure

```
footwear_ecommerce/
├── apps/
│   ├── accounts/          # User management
│   ├── products/          # Product catalog
│   ├── orders/            # Order processing
│   ├── payments/          # Payment processing
│   ├── cart/              # Shopping cart
│   └── cms/              # Content management
├── static/
├── media/
├── templates/
├── requirements.txt
├── manage.py
└── settings/
    ├── base.py
    ├── development.py
    └── production.py
```

## 🔧 Configuration

### M-Pesa Integration Setup

1. **Register with Safaricom Daraja API**
   - Visit https://developer.safaricom.co.ke/
   - Create an app and get Consumer Key and Secret

2. **Configure M-Pesa Settings**
   - Add credentials to environment variables
   - Set up callback URL for payment confirmations
   - Test with sandbox environment first

### County and Delivery Areas Setup

1. **Load Counties**
   - Import all 47 Kenyan counties
   - Set up delivery areas within each county
   - Configure shipping fees per area

2. **Example Data Loading**
```python
# Management command to load counties
python manage.py load_counties
```

## 📱 API Endpoints (if implementing REST API)

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

### Products
- `GET /api/shoes/` - List shoes with filtering
- `GET /api/shoes/{id}/` - Shoe details
- `GET /api/categories/` - Shoe categories
- `GET /api/brands/` - Shoe brands

### Cart & Orders
- `GET /api/cart/` - Get user's cart
- `POST /api/cart/add/` - Add item to cart
- `POST /api/orders/` - Create order
- `GET /api/orders/` - User's orders

### Payments
- `POST /api/payments/mpesa/` - Initiate M-Pesa payment
- `POST /api/payments/callback/` - M-Pesa callback endpoint

## 🎨 Frontend Integration

### Template Context Processors
Add custom context processors for:
- Cart item count
- Available counties and delivery areas
- Site settings
- Featured products

### JavaScript Integration
- AJAX cart updates
- Dynamic size/color selection
- M-Pesa STK Push integration
- Real-time order tracking

## 🔒 Security Considerations

1. **Payment Security**
   - Validate all M-Pesa callbacks
   - Use HTTPS for all payment endpoints
   - Implement proper CSRF protection

2. **User Data Protection**
   - Secure password storage
   - Personal information encryption
   - GDPR compliance considerations

3. **Order Security**
   - Prevent price manipulation
   - Validate stock availability
   - Secure order number generation

## 📈 Performance Optimization

1. **Database Optimization**
   - Add database indexes for frequently queried fields
   - Use select_related and prefetch_related for complex queries
   - Implement database connection pooling

2. **Caching Strategy**
   - Cache product listings and details
   - Session-based cart caching
   - Redis for high-performance caching

3. **Image Optimization**
   - Automatic image resizing
   - WebP format support
   - CDN integration for static files

## 🧪 Testing

### Unit Tests
```bash
python manage.py test
```

### Test Coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🚀 Deployment

### Production Checklist
- [ ] Set DEBUG=False
- [ ] Configure production database
- [ ] Set up static file serving
- [ ] Configure email backend
- [ ] Set up SSL certificates
- [ ] Configure M-Pesa production endpoints
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

### Environment Variables for Production
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@db:5432/footwear_prod
REDIS_URL=redis://redis:6379/0
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Email: support@yourfootwearstore.com
- Documentation: https://docs.yourfootwearstore.com
- Issues: https://github.com/your-username/footwear-ecommerce/issues

## 🙏 Acknowledgments

- Django community for the excellent framework
- Safaricom for M-Pesa API
- Contributors and beta testers
- Open source libraries used in this project