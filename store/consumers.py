from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q
from .models import Product, Category

class ProductChatConsumer(AsyncJsonWebsocketConsumer):
	async def connect(self):
		await self.accept()
		await self.send_json({'type': 'system', 'message': 'Connected. Ask about products, categories, prices, or availability.'})

	async def receive_json(self, content, **kwargs):
		message = (content or {}).get('message', '')
		msg = (message or '').strip().lower()
		if not msg:
			await self.send_json({'type': 'bot', 'message': 'Hi! How can I help you explore products today?'})
			return

		if any(greet in msg for greet in ['hello', 'hi', 'hey']):
			await self.send_json({'type': 'bot', 'message': 'Hello! Ask me about products, categories, prices, or availability.'})
			return

		keywords = [w for w in msg.split() if len(w) > 2]
		products = Product.objects.filter(is_active=True)
		for kw in keywords:
			products = products.filter(Q(title__icontains=kw) | Q(description__icontains=kw))
		products = products.select_related('category')[:5]
		if products:
			lines = []
			for p in products:
				status = 'In stock' if p.in_stock else 'Out of stock'
				lines.append(f"{p.title} (${p.discounted_price}) - {status} in {p.category.name}.")
			await self.send_json({'type': 'bot', 'message': 'Here are some matches: ' + ' '.join(lines)})
			return

		cat = Category.objects.filter(name__icontains=msg).first()
		if cat:
			count = cat.products.filter(is_active=True).count()
			await self.send_json({'type': 'bot', 'message': f'We have {count} product(s) in {cat.name}. Try searching with keywords.'})
			return

		await self.send_json({'type': 'bot', 'message': 'I can help with products, categories, prices, and availability. Try: "phones under 500" or "laptop 16GB".'})