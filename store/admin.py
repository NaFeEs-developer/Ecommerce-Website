from django.contrib import admin
from .models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "is_active", "created_at")
	prepopulated_fields = {"slug": ("name",)}
	search_fields = ("name",)
	list_filter = ("is_active",)


class ProductImageInline(admin.TabularInline):
	model = ProductImage
	extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ("title", "category", "price", "discount_percent", "stock", "is_active")
	list_filter = ("category", "is_active")
	search_fields = ("title", "description")
	prepopulated_fields = {"slug": ("title",)}
	inlines = [ProductImageInline]


class CartItemInline(admin.TabularInline):
	model = CartItem
	extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "session_key", "checked_out", "created_at")
	list_filter = ("checked_out",)
	inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "status", "total", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("id", "user__username", "email")
	inlines = [OrderItemInline]
