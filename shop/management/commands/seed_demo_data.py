from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import Category, Product


class Command(BaseCommand):
    help = "Seed demo categories and products for the fitness shop"

    def handle(self, *args, **options):
        demo_categories = [
            ("Dụng cụ tập gym", "Máy móc và phụ kiện hỗ trợ tập gym tại nhà."),
            ("Yoga", "Thảm, block và dụng cụ hỗ trợ yoga, giãn cơ."),
            ("Chạy bộ", "Phụ kiện và thiết bị cho chạy bộ, cardio."),
        ]

        categories = {}
        for name, description in demo_categories:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            categories[name] = category

        demo_products = [
            {
                "category": "Dụng cụ tập gym",
                "name": "Dumbbell Adjustable Pro",
                "price": Decimal("1290000.00"),
                "description": "Bộ tạ tay điều chỉnh đa nấc, phù hợp tập tại nhà.",
                "stock": 18,
            },
            {
                "category": "Dụng cụ tập gym",
                "name": "Resistance Band Set",
                "price": Decimal("390000.00"),
                "description": "Bộ dây kháng lực đa mức, gọn nhẹ và linh hoạt.",
                "stock": 35,
            },
            {
                "category": "Yoga",
                "name": "Premium Yoga Mat",
                "price": Decimal("490000.00"),
                "description": "Thảm yoga chống trượt, êm và bền cho luyện tập hằng ngày.",
                "stock": 22,
            },
            {
                "category": "Yoga",
                "name": "Yoga Block Foam",
                "price": Decimal("150000.00"),
                "description": "Gạch yoga hỗ trợ căn chỉnh tư thế và kéo giãn.",
                "stock": 40,
            },
            {
                "category": "Chạy bộ",
                "name": "Running Belt",
                "price": Decimal("250000.00"),
                "description": "Đai chạy bộ gọn nhẹ để mang theo điện thoại và chìa khóa.",
                "stock": 30,
            },
            {
                "category": "Chạy bộ",
                "name": "Hydration Bottle",
                "price": Decimal("180000.00"),
                "description": "Bình nước thể thao tiện dụng cho chạy bộ và tập luyện.",
                "stock": 50,
            },
        ]

        created_count = 0
        for item in demo_products:
            product, created = Product.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category": categories[item["category"]],
                    "price": item["price"],
                    "description": item["description"],
                    "stock": item["stock"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                product.category = categories[item["category"]]
                product.price = item["price"]
                product.description = item["description"]
                product.stock = item["stock"]
                product.is_active = True
                product.save()

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(categories)} categories and {created_count} new products."))
