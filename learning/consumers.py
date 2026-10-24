import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import LearningSession
from swaps.models import SwapRequest
from accounts.models import UserBlock

class LearningRoomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        user = self.scope.get("user")
        if not user or not user.is_authenticated or not await self.can_join(user.pk, self.room_id):
            await self.close(code=4403)
            return
        self.group_name = f"learning_{self.room_id.replace('-', '')}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(self.group_name, {"type": "room.event", "payload": {"type": "participant_joined", "user_id": user.pk}})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            user = self.scope.get("user")
            if user and user.is_authenticated:
                await self.channel_layer.group_send(self.group_name, {"type": "room.event", "payload": {"type": "participant_left", "user_id": user.pk}})

    async def receive_json(self, content, **kwargs):
        # Re-check authorization for every event, not only when the socket opens.
        user = self.scope.get("user")
        if not user or not user.is_authenticated or not await self.can_join(user.pk, self.room_id):
            await self.close(code=4403)
            return
        # Clients must only send the supported signaling/chat event types.
        event_type = content.get("type")
        if event_type not in {"offer", "answer", "ice_candidate", "chat_ciphertext", "chat_key_fingerprint", "screen_share_status", "media_status", "ping"}:
            await self.send_json({"type": "error", "message": "Unsupported event type."})
            return
        # Never persist signaling payloads or encrypted chat by default.
        payload = {"type": event_type, "sender_id": self.scope["user"].pk, "data": content.get("data", {})}
        await self.channel_layer.group_send(self.group_name, {"type": "room.event", "payload": payload, "exclude_channel": self.channel_name})

    async def room_event(self, event):
        if event.get("exclude_channel") == self.channel_name:
            return
        await self.send_json(event["payload"])

    @database_sync_to_async
    def can_join(self, user_id, room_id):
        try:
            session = LearningSession.objects.select_related("swap_request").get(pk=room_id)
        except (LearningSession.DoesNotExist, ValueError):
            return False
        swap = session.swap_request
        if swap.status != SwapRequest.ACCEPTED or user_id not in (swap.from_user_id, swap.to_user_id):
            return False
        other_id = swap.to_user_id if user_id == swap.from_user_id else swap.from_user_id
        return not (UserBlock.objects.filter(blocker_id=user_id, blocked_id=other_id).exists() or UserBlock.objects.filter(blocker_id=other_id, blocked_id=user_id).exists())
