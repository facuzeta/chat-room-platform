# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http  
import group_manager.models
from channels.db import database_sync_to_async
import bot.models
import logging

logger = logging.getLogger(__name__)

async def connect(self):
    self.username = await self.get_name()

@database_sync_to_async
def get_name(self):
    return User.objects.all()[0].name

@database_sync_to_async
def store_chat(user, stage_name, message):
    logger.info(f'store_chat participant.id: {participant.id}, stage_name: {stage_name}, message: {message}')

    participant = group_manager.models.Participant.objects.get(user=user)
    stage = group_manager.models.Stage.objects.get(name=stage_name)
    group_manager.models.Chat.objects.create(text=message, participant=participant, stage=stage)

@database_sync_to_async
def get_nickname_and_color(user):
    participant = group_manager.models.Participant.objects.get(user=user)

    nickname = participant.get_nickname()
    color = participant.get_color()
    return nickname, color

@database_sync_to_async
def get_all_bots_in_same_group(user):    
    participant = group_manager.models.Participant.objects.get(user=user)    
    participant_bots_in_group = [p for p in participant.group.participants.all() if p.is_bot()]
    return participant_bots_in_group

@database_sync_to_async
def get_bot(behaviour_nickname):
    current_bot = bot.models.Bot.objects.get(behaviour_nickname=behaviour_nickname)
    return current_bot

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
        logger.info(f'receive stage_name: {stage_name}, message: {message}')

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
                'user_id':self.user.id,
                'is_bot':False
                # 'user': self.user.username+'('+str(self.user.id)+')'
            }
        ) 
        
        

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        color = event['color']
        user_id = event['user_id']
        bot_msg = event['is_bot']
        own_msg = (user_id == self.user.id and not(bot_msg))        
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
        logger.info(f'receive stage_name: {stage_name}, message: {message}')

        

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