from django.core.management.base import BaseCommand
from ecommerce.models import County, DeliveryArea
from decimal import Decimal

class Command(BaseCommand):
    help = "Seed 5 Kenyan counties with delivery areas and shipping fees"

    def handle(self, *args, **kwargs):
        counties_data = [
            {
                "name": "Nairobi",
                "code": "047",
                "areas": [
                    {"name": "Westlands", "shipping_fee": Decimal("200.00"), "delivery_days": 1},
                    {"name": "Kasarani", "shipping_fee": Decimal("180.00"), "delivery_days": 2},
                    {"name": "Langata", "shipping_fee": Decimal("220.00"), "delivery_days": 1},
                ],
            },
            {
                "name": "Mombasa",
                "code": "001",
                "areas": [
                    {"name": "Nyali", "shipping_fee": Decimal("250.00"), "delivery_days": 2},
                    {"name": "Likoni", "shipping_fee": Decimal("230.00"), "delivery_days": 3},
                    {"name": "Mvita", "shipping_fee": Decimal("200.00"), "delivery_days": 2},
                ],
            },
            {
                "name": "Kisumu",
                "code": "042",
                "areas": [
                    {"name": "Kisumu Central", "shipping_fee": Decimal("210.00"), "delivery_days": 2},
                    {"name": "Muhoroni", "shipping_fee": Decimal("240.00"), "delivery_days": 3},
                    {"name": "Nyando", "shipping_fee": Decimal("220.00"), "delivery_days": 2},
                ],
            },
            {
                "name": "Nakuru",
                "code": "032",
                "areas": [
                    {"name": "Naivasha", "shipping_fee": Decimal("200.00"), "delivery_days": 2},
                    {"name": "Njoro", "shipping_fee": Decimal("210.00"), "delivery_days": 3},
                    {"name": "Gilgil", "shipping_fee": Decimal("220.00"), "delivery_days": 2},
                ],
            },
            {
                "name": "Kiambu",
                "code": "022",
                "areas": [
                    {"name": "Thika", "shipping_fee": Decimal("180.00"), "delivery_days": 2},
                    {"name": "Ruiru", "shipping_fee": Decimal("200.00"), "delivery_days": 1},
                    {"name": "Limuru", "shipping_fee": Decimal("210.00"), "delivery_days": 2},
                ],
            },
        ]

        for county_data in counties_data:
            county, created = County.objects.get_or_create(
                name=county_data["name"],
                code=county_data["code"],
                defaults={"is_active": True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created county: {county.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"County already exists: {county.name}"))

            for area in county_data["areas"]:
                delivery_area, area_created = DeliveryArea.objects.get_or_create(
                    name=area["name"],
                    county=county,
                    defaults={
                        "shipping_fee": area["shipping_fee"],
                        "delivery_days": area["delivery_days"],
                        "is_active": True,
                    }
                )
                if area_created:
                    self.stdout.write(self.style.SUCCESS(f"  Added area: {delivery_area.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"  Area already exists: {delivery_area.name}"))
