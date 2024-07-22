from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from bot.models import Bot
from bot.api.serializer import BotSerializer

@api_view(['GET', 'POST'])
def bot_list(request):
    """
    List all code bots, or create a new bot.
    """
    if request.method == 'GET':
        bots = Bot.objects.all()
        serializer = BotSerializer(bots, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = BotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET', 'PUT', 'DELETE', 'POST'])
def bot_detail(request, pk):
    """
    Retrieve, update or delete a code bot.

    With POST, you can send a message and receive a response
    """
    try:
        bot = Bot.objects.get(pk=pk)
    except Bot.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BotSerializer(bot)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = BotSerializer(bot, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        bot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    elif request.method == 'POST':  
        input_chat = str(request.data.get("prompt"))
        return Response({"response": input_chat + input_chat, "made_by": bot.behaviour_nickname},status = status.HTTP_200_OK)
    
