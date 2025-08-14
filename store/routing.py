from django.urls import path
from .consumers import ProductChatConsumer

websocket_urlpatterns = [
	path('ws/chat/', ProductChatConsumer.as_asgi()),
]