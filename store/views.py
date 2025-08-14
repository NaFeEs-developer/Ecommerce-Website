from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import Category, Product, Cart, CartItem, Order, OrderItem
from django.conf import settings

try:
	import stripe
	stripe.api_key = settings.STRIPE_SECRET_KEY
except Exception:
	stripe = None


def _get_or_create_cart(request: HttpRequest) -> Cart:
	if request.user.is_authenticated:
		cart, _ = Cart.objects.get_or_create(user=request.user, checked_out=False)
		return cart
	if not request.session.session_key:
		request.session.create()
	session_key = request.session.session_key
	cart, _ = Cart.objects.get_or_create(session_key=session_key, checked_out=False)
	return cart


def home(request: HttpRequest) -> HttpResponse:
	query = request.GET.get('q', '').strip()
	products = Product.objects.filter(is_active=True)
	if query:
		products = products.filter(Q(title__icontains=query) | Q(description__icontains=query))
	categories = Category.objects.filter(is_active=True)
	return render(request, 'store/home.html', {
		'products': products.select_related('category')[:24],
		'categories': categories,
		'query': query,
	})


def category_detail(request: HttpRequest, slug: str) -> HttpResponse:
	category = get_object_or_404(Category, slug=slug, is_active=True)
	products = category.products.filter(is_active=True)
	return render(request, 'store/category_detail.html', {'category': category, 'products': products})


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
	product = get_object_or_404(Product, slug=slug, is_active=True)
	images = product.images.all()
	return render(request, 'store/product_detail.html', {'product': product, 'images': images})


@require_POST
def add_to_cart(request: HttpRequest, slug: str) -> HttpResponse:
	cart = _get_or_create_cart(request)
	product = get_object_or_404(Product, slug=slug, is_active=True)
	quantity = int(request.POST.get('quantity', '1'))
	item, created = CartItem.objects.get_or_create(cart=cart, product=product)
	if not created:
		item.quantity += quantity
	else:
		item.quantity = quantity
	item.save()
	return redirect('cart_detail')


def cart_detail(request: HttpRequest) -> HttpResponse:
	cart = _get_or_create_cart(request)
	items = cart.items.select_related('product').all()
	return render(request, 'store/cart.html', {'cart': cart, 'items': items})


@require_POST
def update_cart_item(request: HttpRequest, item_id: int) -> HttpResponse:
	cart = _get_or_create_cart(request)
	item = get_object_or_404(CartItem, id=item_id, cart=cart)
	quantity = int(request.POST.get('quantity', '1'))
	if quantity <= 0:
		item.delete()
	else:
		item.quantity = quantity
		item.save()
	return redirect('cart_detail')


@login_required
@require_POST
def checkout(request: HttpRequest) -> HttpResponse:
	cart = _get_or_create_cart(request)
	items = list(cart.items.select_related('product'))
	if not items:
		return redirect('cart_detail')
	total = sum([i.subtotal for i in items])
	order = Order.objects.create(
		user=request.user,
		cart=cart,
		total=total,
		full_name=request.POST.get('full_name', request.user.get_full_name() or request.user.username),
		email=request.POST.get('email', request.user.email),
		phone=request.POST.get('phone', ''),
		address_line1=request.POST.get('address_line1', ''),
		address_line2=request.POST.get('address_line2', ''),
		city=request.POST.get('city', ''),
		state=request.POST.get('state', ''),
		postal_code=request.POST.get('postal_code', ''),
		country=request.POST.get('country', ''),
	)
	for item in items:
		OrderItem.objects.create(order=order, product=item.product, unit_price=item.product.discounted_price, quantity=item.quantity)
		item.product.stock = max(0, item.product.stock - item.quantity)
		item.product.save()
	cart.checked_out = True
	cart.save()
	return render(request, 'store/order_success.html', {'order': order})


@login_required
@require_POST
def stripe_checkout(request: HttpRequest) -> HttpResponse:
	cart = _get_or_create_cart(request)
	items = list(cart.items.select_related('product'))
	if not items:
		return redirect('cart_detail')
	if stripe and settings.STRIPE_PUBLIC_KEY and settings.STRIPE_SECRET_KEY:
		line_items = []
		for i in items:
			line_items.append({
				'price_data': {
					'currency': 'usd',
					'product_data': {'name': i.product.title},
					'unit_amount': int(i.product.discounted_price * 100)
				},
				'quantity': i.quantity,
			})
			session = stripe.checkout.Session.create(
				mode='payment',
				line_items=line_items,
				success_url=request.build_absolute_uri('/checkout/success/'),
				cancel_url=request.build_absolute_uri('/cart/'),
			)
			return redirect(session.url)
	# Fallback: simulate successful payment using normal checkout flow
	return checkout(request)


def checkout_success(request: HttpRequest) -> HttpResponse:
	return render(request, 'store/order_success.html', {'order': None})


def register_view(request: HttpRequest) -> HttpResponse:
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('home')
	else:
		form = UserCreationForm()
	return render(request, 'store/register.html', {'form': form})


def login_view(request: HttpRequest) -> HttpResponse:
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			return redirect('home')
	else:
		form = AuthenticationForm(request)
	return render(request, 'store/login.html', {'form': form})


def logout_view(request: HttpRequest) -> HttpResponse:
	logout(request)
	return redirect('home')


# Simple rule-based product chat restricted to on-site products
def product_chat_api(request: HttpRequest) -> JsonResponse:
	if request.method != 'POST':
		return JsonResponse({'error': 'Method not allowed'}, status=405)
	payload = request.POST
	message = (payload.get('message') or '').strip().lower()
	if not message:
		return JsonResponse({'reply': 'Hi! How can I help you explore products today?'})

	# Very simple intent handling
	if any(greet in message for greet in ['hello', 'hi', 'hey']):
		return JsonResponse({'reply': 'Hello! Ask me about products, categories, prices, or availability.'})

	# Search products by title keywords
	keywords = [w for w in message.split() if len(w) > 2]
	products = Product.objects.filter(is_active=True)
	for kw in keywords:
		products = products.filter(Q(title__icontains=kw) | Q(description__icontains=kw))
	products = products.select_related('category')[:5]
	if products:
		replies = []
		for p in products:
			status = 'In stock' if p.in_stock else 'Out of stock'
			price = p.discounted_price
			replies.append(f"{p.title} (${price}) - {status} in {p.category.name}.")
		return JsonResponse({'reply': 'Here are some matches: ' + ' '.join(replies)})

	# Category mention
	cat = Category.objects.filter(name__icontains=message).first()
	if cat:
		count = cat.products.filter(is_active=True).count()
		return JsonResponse({'reply': f"We have {count} product(s) in {cat.name}. Try searching with keywords."})

	# Help fallback
	return JsonResponse({'reply': 'I can help with products, categories, prices, and availability. Try: "phones under 500" or "laptop 16GB".'})
