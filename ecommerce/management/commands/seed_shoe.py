import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from ecommerce.models import Shoe, ShoeCategory, Brand, ShoeSize, Color


class Command(BaseCommand):
    help = "Seed 30 sample shoes into the database"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding 30 shoes..."))

        categories = list(ShoeCategory.objects.all())
        brands = list(Brand.objects.all())
        sizes = list(ShoeSize.objects.all())
        colors = list(Color.objects.all())

        if not categories or not brands or not sizes or not colors:
            self.stdout.write(self.style.ERROR(
                "❌ Please seed ShoeCategory, Brand, ShoeSize, and Color first!"
            ))
            return

        # Predefined shoe names (mixing for men, women, unisex, kids)
        shoe_names = [
            "Air Runner", "Street Kicks", "Classic Leather", "Urban Boots", "Pro Trainers",
            "Elite Sneakers", "Daily Walkers", "High Top Energy", "Lightweight Runners", "Mountain Trek",
            "Canvas Classics", "Formal Derby", "Casual Slip-On", "Active Sports", "Comfort Slides",
            "Trail Blazer", "Rapid Jogger", "Vintage Court", "City Runner", "Power Cleats",
            "Skater Pro", "All Weather Boot", "Premium Loafers", "Everyday Sneakers", "Sprint Max",
            "Court Master", "Training Pro", "Chill Sandals", "Grip Hiker", "Kids Fun Runner"
        ]

        Shoe.objects.all().delete()  # optional: clean slate
        self.stdout.write(self.style.WARNING("⚠️ Deleted existing shoes."))

        for i, name in enumerate(shoe_names, start=1):
            brand = random.choice(brands)
            category = random.choice(categories)
            gender = random.choice([choice[0] for choice in Shoe.GENDER_CHOICES])
            base_price = random.choice([3500, 4500, 5500, 6000, 7500, 8500, 9999])
            compare_price = base_price + random.choice([500, 1000, 1500])

            shoe = Shoe.objects.create(
                name=name,
                slug=slugify(f"{name}-{i}"),
                description=f"{name} is designed for comfort, durability, and style.",
                short_description=f"Stylish {name} for {gender}.",
                sku=f"SHOE-{1000+i}",
                category=category,
                brand=brand,
                gender=gender,
                base_price=base_price,
                compare_price=compare_price,
                material=random.choice(["Leather", "Canvas", "Synthetic", "Mesh"]),
                sole_material=random.choice(["Rubber", "Foam", "EVA", "TPU"]),
                features=random.choice([
                    "Breathable and lightweight",
                    "Waterproof with extra grip",
                    "Premium cushioning",
                    "Durable high-top design",
                    "Classic retro vibe"
                ]),
                meta_title=f"{name} - {brand.name}",
                meta_description=f"Buy {name} from {brand.name}. Perfect shoes for {gender}.",
                status="active",
                is_featured=random.choice([True, False]),
                is_new_arrival=random.choice([True, False]),
                is_on_sale=random.choice([True, False]),
                is_trending=random.choice([True, False]),
            )

            # Assign random sizes (3–5 sizes per shoe)
            shoe.available_sizes.set(random.sample(sizes, k=min(5, len(sizes))))
            # Assign random colors (2–3 colors per shoe)
            shoe.available_colors.set(random.sample(colors, k=min(3, len(colors))))

            self.stdout.write(self.style.SUCCESS(f"✅ Created {shoe.name}"))

        self.stdout.write(self.style.SUCCESS("🎉 Successfully seeded 30 shoes!"))
