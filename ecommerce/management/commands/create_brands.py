import random
from django.core.management.base import BaseCommand
from ecommerce.models import Brand
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Generate 8 shoe brands"

    def handle(self, *args, **kwargs):
        brands = [
            {"name": "Nike", "website": "https://www.nike.com"},
            {"name": "Adidas", "website": "https://www.adidas.com"},
            {"name": "Puma", "website": "https://www.puma.com"},
            {"name": "Reebok", "website": "https://www.reebok.com"},
            {"name": "New Balance", "website": "https://www.newbalance.com"},
            {"name": "Asics", "website": "https://www.asics.com"},
            {"name": "Converse", "website": "https://www.converse.com"},
            {"name": "Vans", "website": "https://www.vans.com"},
        ]

        for data in brands:
            brand, created = Brand.objects.get_or_create(
                name=data["name"],
                defaults={
                    "slug": slugify(data["name"]),
                    "description": f"{data['name']} official footwear brand.",
                    "website": data["website"],
                    "is_active": True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Brand '{brand.name}' created successfully"))
            else:
                self.stdout.write(self.style.WARNING(f"Brand '{brand.name}' already exists"))
