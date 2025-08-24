import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from ecommerce.models import ShoeCategory  # <-- change `shop` to your app name


class Command(BaseCommand):
    help = "Generate 5 default shoe categories"

    def handle(self, *args, **kwargs):
        categories = [
            {"name": "Sneakers", "description": "Casual and stylish sneakers for everyday wear."},
            {"name": "Formal", "description": "Elegant formal shoes for business and special occasions."},
            {"name": "Boots", "description": "Durable boots for outdoor and casual styles."},
            {"name": "Sandals", "description": "Light and comfortable sandals for warm weather."},
            {"name": "Sports", "description": "Shoes designed for running, training, and performance."},
        ]

        for index, cat in enumerate(categories, start=1):
            obj, created = ShoeCategory.objects.get_or_create(
                name=cat["name"],
                defaults={
                    "slug": slugify(cat["name"]),
                    "description": cat["description"],
                    "sort_order": index,
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created category: {obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Category already exists: {obj.name}"))
