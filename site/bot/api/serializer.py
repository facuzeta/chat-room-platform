from rest_framework import serializers
from bot.models import Bot

class BotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bot        
        fields = ['id', 'system_prompt', 'reply_probability', 'behaviour_nickname', 'llmodel']