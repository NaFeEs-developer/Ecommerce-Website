from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class Category(models.Model):
	name = models.CharField(max_length=80, unique=True)
	slug = models.SlugField(max_length=100, unique=True, blank=True)
	icon = models.CharField(max_length=80, blank=True, help_text="CSS icon class or emoji")
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		return super().save(*args, **kwargs)

	def __str__(self) -> str:
		return self.name


class Product(models.Model):
	category = models.ForeignKey(Category, related_name='products', on_delete=models.PROTECT)
	title = models.CharField(max_length=160)
	slug = models.SlugField(max_length=180, unique=True, blank=True)
	description = models.TextField()
	price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	discount_percent = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
	stock = models.PositiveIntegerField(default=0)
	thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.title)
		return super().save(*args, **kwargs)

	@property
	def discounted_price(self):
		if self.discount_percent:
			return round(self.price * (100 - self.discount_percent) / 100, 2)
		return self.price

	@property
	def in_stock(self) -> bool:
		return self.stock > 0 and self.is_active

	def __str__(self) -> str:
		return self.title


class ProductImage(models.Model):
	product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
	image = models.ImageField(upload_to='products/gallery/')
	alt_text = models.CharField(max_length=160, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"Image for {self.product.title}"


class Cart(models.Model):
	user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
	session_key = models.CharField(max_length=40, blank=True, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	checked_out = models.BooleanField(default=False)

	class Meta:
		indexes = [models.Index(fields=['session_key'])]

	def __str__(self):
		owner = self.user.username if self.user else self.session_key
		return f"Cart({owner})"

	def total_amount(self):
		items = self.items.select_related('product')
		return sum((item.subtotal for item in items), start=0)


class CartItem(models.Model):
	cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
	added_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('cart', 'product')

	@property
	def subtotal(self):
		price = self.product.discounted_price
		return round(price * self.quantity, 2)

	def __str__(self):
		return f"{self.quantity} x {self.product.title}"


class Order(models.Model):
	PENDING = 'PENDING'
	PAID = 'PAID'
	SHIPPED = 'SHIPPED'
	CANCELLED = 'CANCELLED'
	STATUS_CHOICES = [
		(PENDING, 'Pending'),
		(PAID, 'Paid'),
		(SHIPPED, 'Shipped'),
		(CANCELLED, 'Cancelled'),
	]

	user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='orders')
	cart = models.OneToOneField(Cart, on_delete=models.PROTECT, related_name='order')
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
	total = models.DecimalField(max_digits=12, decimal_places=2)
	full_name = models.CharField(max_length=160)
	email = models.EmailField()
	phone = models.CharField(max_length=40)
	address_line1 = models.CharField(max_length=160)
	address_line2 = models.CharField(max_length=160, blank=True)
	city = models.CharField(max_length=80)
	state = models.CharField(max_length=80)
	postal_code = models.CharField(max_length=20)
	country = models.CharField(max_length=60)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Order #{self.id} - {self.user} - {self.status}"


class OrderItem(models.Model):
	order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.PROTECT)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

	@property
	def line_total(self):
		return round(self.unit_price * self.quantity, 2)

	def __str__(self):
		return f"{self.product.title} x {self.quantity}"
