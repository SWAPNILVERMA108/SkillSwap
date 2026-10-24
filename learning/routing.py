from django.urls import path
from .consumers import LearningRoomConsumer
websocket_urlpatterns = [path("ws/learning/<uuid:room_id>/", LearningRoomConsumer.as_asgi())]
