from .models import Category, Cart

def global_context(request):
	categories = Category.objects.filter(is_active=True)[:20]
	cart_count = 0
	try:
		from .views import _get_or_create_cart
		cart = _get_or_create_cart(request)
		cart_count = cart.items.count()
	except Exception:
		cart_count = 0
	return {
		'global_categories': categories,
		'cart_count': cart_count,
	}