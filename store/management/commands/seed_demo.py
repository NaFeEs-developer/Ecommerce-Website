from django.core.management.base import BaseCommand
from django.conf import settings
from store.models import Category, Product, ProductImage
from pathlib import Path
from random import randint, choice
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
import textwrap


class Command(BaseCommand):
	help = 'Seed the database with demo categories and products.'

	def handle(self, *args, **options):
		self.stdout.write('Seeding demo data...')

		categories = [
			('Electronics', '📱'),
			('Laptops', '💻'),
			('Phones', '📱'),
			('Accessories', '🎧'),
			('Fashion', '👟'),
		]

		cat_objs = {}
		for name, icon in categories:
			cat, _ = Category.objects.get_or_create(name=name, defaults={'icon': icon, 'is_active': True})
			cat_objs[name] = cat

		products = [
			('Nova Phone X', 'Phones', 'Flagship phone with stunning camera and battery life.'),
			('AeroBook 14', 'Laptops', 'Ultra-light laptop with 11th‑gen CPU and 16GB RAM.'),
			('BassMax Headphones', 'Accessories', 'Wireless over-ear headphones with ANC.'),
			('Urban Sneaker', 'Fashion', 'Comfortable sneakers for daily wear.'),
			('4K Action Cam', 'Electronics', 'Shoot epic adventures in 4K with stabilization.'),
		]

		media_root = Path(settings.MEDIA_ROOT)
		(media_root / 'seed').mkdir(parents=True, exist_ok=True)

		def make_image(text: str, filename: str) -> str:
			path = media_root / 'seed' / filename
			if path.exists():
				return str(path.relative_to(media_root))
			img = Image.new('RGB', (800, 600), color=(randint(10,50), randint(10,50), randint(60,120)))
			draw = ImageDraw.Draw(img)
			wrap = textwrap.fill(text, width=14)
			try:
				font = ImageFont.load_default()
			except Exception:
				font = None
			draw.text((30, 250), wrap, fill=(240,240,255), font=font)
			img.save(path, format='JPEG', quality=86)
			return str(path.relative_to(media_root))

		count = 0
		for title, cat_name, desc in products:
			cat = cat_objs[cat_name]
			price = Decimal(randint(49, 1499))
			discount = choice([0, 5, 10, 15, 20])
			stock = randint(5, 40)
			thumb_rel = make_image(title, f"{title.lower().replace(' ','_')}_thumb.jpg")
			p, created = Product.objects.get_or_create(
				title=title,
				defaults={
					'category': cat,
					'description': desc,
					'price': price,
					'discount_percent': discount,
					'stock': stock,
					'thumbnail': thumb_rel and f'seed/{Path(thumb_rel).name}',
				}
			)
			if created:
				# Add 2 gallery images
				for i in range(2):
					img_rel = make_image(f"{title} gallery {i+1}", f"{title.lower().replace(' ','_')}_g{i+1}.jpg")
					ProductImage.objects.create(product=p, image=f"seed/{Path(img_rel).name}")
				count += 1

		self.stdout.write(self.style.SUCCESS(f'Seeded {count} new products.'))