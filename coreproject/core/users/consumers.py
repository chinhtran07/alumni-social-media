import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer

from core.users import daos


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join the room group
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Receive message from WebSocket
        text_data_json = json.loads(text_data)
        payload = text_data_json['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'payload': payload
        }))

    async def send_notification(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'payload': event['payload']
        }))


class UserActivityConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        user_id = data.get('user_id')

        self.send_activity_status_to_friends(user_id)

    def send_activity_status_to_friends(self, user_id):
        # Logic to get friends and send status
        friends = self.get_friends(user_id)
        for friend in friends:
            self.send(text_data=json.dumps({
                'user_id': user_id,
                'status': 'active'
            }))

    def get_friends(self, user_id):
        return daos.FriendshipDAO.get_friends(user_id)
