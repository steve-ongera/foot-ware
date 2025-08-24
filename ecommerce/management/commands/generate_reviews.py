import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ecommerce.models import Shoe, ShoeVariant, Review

User = get_user_model()


class Command(BaseCommand):
    help = "Generate 1–5 reviews per shoe"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding reviews for shoes..."))

        shoes = Shoe.objects.all()
        users = list(User.objects.all())

        if not shoes.exists():
            self.stdout.write(self.style.ERROR("❌ No shoes found. Seed shoes first!"))
            return

        if not users:
            self.stdout.write(self.style.ERROR("❌ No users found. Please create some users first!"))
            return

        count = 0
        for shoe in shoes:
            num_reviews = random.randint(1, 5)
            for _ in range(num_reviews):
                user = random.choice(users)

                # Skip if this user already reviewed this shoe (unique_together constraint)
                if Review.objects.filter(shoe=shoe, user=user).exists():
                    continue

                variant = random.choice(list(shoe.variants.all())) if shoe.variants.exists() else None
                rating = random.randint(1, 5)

                review = Review.objects.create(
                    shoe=shoe,
                    user=user,
                    variant=variant,
                    rating=rating,
                    title=random.choice([
                        "Amazing shoes!", "Very comfortable", "Not bad", 
                        "Could be better", "Totally worth it", "Disappointed"
                    ]),
                    content=random.choice([
                        "These shoes are fantastic, great value for money.",
                        "Pretty good overall, fits nicely.",
                        "Quality could be better, but still okay.",
                        "Absolutely love these! Super comfy.",
                        "Not what I expected, but works for casual use."
                    ]),
                    fit_rating=random.randint(3, 5),
                    comfort_rating=random.randint(2, 5),
                    quality_rating=random.randint(2, 5),
                    is_approved=random.choice([True, False]),
                    is_verified_purchase=random.choice([True, False]),
                    helpful_count=random.randint(0, 20),
                )

                count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Added review for {shoe.name} by {user.username}"))

        self.stdout.write(self.style.SUCCESS(f"🎉 Successfully created {count} reviews!"))
