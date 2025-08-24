import random
from django.core.management.base import BaseCommand
from ecommerce.models import ShoeSize, Color


class Command(BaseCommand):
    help = "Seed shoe sizes and colors into the database"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding shoe sizes and colors..."))

        # --- Shoe Sizes ---
        sizes = {
            "US": ["6", "7", "8", "9", "10", "11", "12"],
            "UK": ["5", "6", "7", "8", "9", "10", "11"],
            "EU": ["39", "40", "41", "42", "43", "44", "45"],
        }

        for system, size_list in sizes.items():
            for order, size in enumerate(size_list):
                obj, created = ShoeSize.objects.get_or_create(
                    size=size,
                    system=system,
                    defaults={"sort_order": order}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Added {obj}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Already exists: {obj}"))

        # --- Colors ---
        colors = {
            "Red": "#FF0000",
            "Blue": "#0000FF",
            "Black": "#000000",
            "White": "#FFFFFF",
            "Green": "#008000",
            "Yellow": "#FFFF00",
            "Gray": "#808080",
        }

        for name, hex_code in colors.items():
            obj, created = Color.objects.get_or_create(
                name=name,
                defaults={"hex_code": hex_code}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added color {obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists: {obj.name}"))

        self.stdout.write(self.style.SUCCESS("✅ Seeding complete!"))
