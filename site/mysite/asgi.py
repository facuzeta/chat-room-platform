# mysite/asgi.py
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django_asgi_app = get_asgi_application()

from django.urls import path

from chat import views
from chat import views, consumers
from django.urls import re_path

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
         [    
             path('chat/', views.index, name='index'),
             path('chat/<str:room_name>/', views.room, name='room'),
             re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
             re_path(r'ws/chatfortest/(?P<room_name>\w+)/$', consumers.ChatConsumerForTest.as_asgi()),
        ]   
         )
    ),
 
})
# esto lo ejecuta ok daphne -b :: -p 5000  mysite.asgi:application


# import os
# import django
# from channels.routing import get_default_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# django.setup()

# application = get_default_application()

