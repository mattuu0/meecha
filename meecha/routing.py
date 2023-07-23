from django.urls import path
 
from .consumers import ChatConsumer
 
websocket_urlpatterns = [
    path("ws/connect", ChatConsumer.as_asgi()),
]