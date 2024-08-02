from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from bot.models import Bot
from bot.api.serializer import BotSerializer
from django.contrib.admin.views.decorators import staff_member_required

@api_view(['GET'])
@staff_member_required
def bot_list(request):
    """
    List all code bots
    """
    if request.method == 'GET':
        bots = Bot.objects.all()
        serializer = BotSerializer(bots, many=True)
        return Response(serializer.data)    
    
@api_view(['GET', 'POST'])
@staff_member_required
def bot_detail(request, pk):
    """
    GET to retrieve a bot.

    POST to send prompt to bot and receive a response
    """
    try:
        bot = Bot.objects.get(pk=pk)
    except Bot.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BotSerializer(bot)
        return Response(serializer.data)   
    
    elif request.method == 'POST': 
        #Here we process the prompt received
        input_chat = str(request.data.get("prompt"))    
        if(bot.behaviour_nickname == "repeat"):
            return Response({"response": input_chat + input_chat, "made_by": bot.behaviour_nickname},status = status.HTTP_200_OK)
        elif (bot.behaviour_nickname == "hello"):
            return Response({"response": "hello", "made_by": bot.behaviour_nickname},status = status.HTTP_200_OK)
        
        
    
