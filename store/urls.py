from django.urls import path
from . import views

urlpatterns = [
	path('', views.home, name='home'),
	path('category/<slug:slug>/', views.category_detail, name='category_detail'),
	path('product/<slug:slug>/', views.product_detail, name='product_detail'),
	path('cart/', views.cart_detail, name='cart_detail'),
	path('cart/add/<slug:slug>/', views.add_to_cart, name='add_to_cart'),
	path('cart/item/<int:item_id>/update/', views.update_cart_item, name='update_cart_item'),
	path('checkout/', views.checkout, name='checkout'),
	path('checkout/stripe/', views.stripe_checkout, name='stripe_checkout'),
	path('checkout/success/', views.checkout_success, name='checkout_success'),
	path('register/', views.register_view, name='register'),
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),
	path('api/chat/', views.product_chat_api, name='product_chat_api'),
]