import random
from django.core.management.base import BaseCommand
from ecommerce.models import Shoe, ShoeVariant


class Command(BaseCommand):
    help = "Generate variants (color + size) for all shoes"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Generating shoe variants..."))

        ShoeVariant.objects.all().delete()
        self.stdout.write(self.style.WARNING("⚠️ Deleted existing shoe variants."))

        shoes = Shoe.objects.all()
        if not shoes.exists():
            self.stdout.write(self.style.ERROR("❌ No shoes found. Seed shoes first!"))
            return

        count = 0
        for shoe in shoes:
            colors = shoe.available_colors.all()
            sizes = shoe.available_sizes.all()

            if not colors or not sizes:
                self.stdout.write(self.style.WARNING(
                    f"Skipping {shoe.name} (no sizes/colors linked)"
                ))
                continue

            for color in colors:
                for size in sizes:
                    variant, created = ShoeVariant.objects.get_or_create(
                        shoe=shoe,
                        color=color,
                        size=size,
                        defaults={
                            "stock_quantity": random.randint(5, 30),
                            "price_adjustment": random.choice([0, 100, 200, -100]),
                            "is_active": True,
                        }
                    )
                    if created:
                        count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Created {variant}")
                        )

        self.stdout.write(self.style.SUCCESS(
            f"🎉 Successfully generated {count} shoe variants!"
        ))
