# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http  
import group_manager.models
from channels.db import database_sync_to_async


async def connect(self):
    self.username = await self.get_name()

@database_sync_to_async
def get_name(self):
    return User.objects.all()[0].name

@database_sync_to_async
def store_chat(user, stage_name, message):
    print('store_chat',user, stage_name, message)
    participant = group_manager.models.Participant.objects.get(user=user)
    print(group_manager.models.Participant)
    print(group_manager.models.Stage)
    stage = group_manager.models.Stage.objects.get(name=stage_name)
    group_manager.models.Chat.objects.create(text=message, participant=participant, stage=stage)

@database_sync_to_async
def get_nickname_and_color(user):
    participant = group_manager.models.Participant.objects.get(user=user)

    nickname = participant.get_nickname()
    color = participant.get_color()
    return nickname, color

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        self.user = self.scope['user']
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        stage_name = text_data_json['stage_name']
        # timestamp = text_data_json['timestamp']
        print('recieve', stage_name, message)

        await store_chat(self.user, stage_name, message)
        nickname, color = await get_nickname_and_color(self.user)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': nickname,
                'color': color,
                'user_id':self.user.id
                # 'user': self.user.username+'('+str(self.user.id)+')'
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        color = event['color']
        user_id = event['user_id']
        own_msg = user_id == self.user.id
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
            'color': color,
            'own_msg': own_msg
        }))


class ChatConsumerForTest(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        self.user = self.scope['user']
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        stage_name = text_data_json['stage_name']
        # timestamp = text_data_json['timestamp']
        print('recieve', stage_name, message)


        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id':self.user.id
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
        }))