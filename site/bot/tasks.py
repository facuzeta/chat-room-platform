from celery import shared_task
from channels.layers import get_channel_layer
import random
from group_manager.services import *
import asyncio
import time
import django
import os

def import_django_instance():
    """
    Makes django environment available 
    to tasks!!
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    django.setup()

@shared_task(bind=True, max_retries=None)
def celery_run_bot(self, data):
    #celery puede recibir solo json data, para obtener el participante carga django y busca por id
    import_django_instance()    
    from group_manager.models import Participant
    pk = data.get('pk')
    print("Bot participant"+ str(pk))
    bot = Participant.objects.get(id=pk)
    bot_current_stage = get_stage_and_change(bot)    
    room_group = "chat_"+ bot.group.name       
    channel_layer = get_channel_layer()
    #El bot se queda en s1 hasta que todos los participantes terminen las encuestas 
    if bot_current_stage.name == 's1' and bot.group != None:
        print("Bot waiting for participants to end stage s1")    
        bot_current_stage = get_stage_and_change(bot)
        self.retry(args=[data], countdown=2)        
        
    #El bot checkea el chat y responde mientras esten en stage de conversacion
    if bot_current_stage.name != 's3'and bot.group != None:
        bot_current_stage = get_stage_and_change(bot)
        if bot_current_stage.name in ['s2_1', 's2_2', 's2_3', 's2_4']:    
                                   
            if bot.bot.reply_probability > random.uniform(0, 1):
                print("Bot coin flip success, calling response")                   
                bot_response = bot.message_bot()                 
                print("Got this response [" + bot_response + "], sending it to chat")                      
                #Si el LLM tarda mucho en hacer la respuesta y cambia el stage, no manda el mensaje
                stage_after_think = get_stage_and_change(bot)
                if bot_current_stage == stage_after_think:
                    #Esto es para dividir el mensaje que manda si ignora el prompt y es muy largo        
                    phrases = bot_response.split(".")
                    for p in phrases: 
                        if p != "":
                            store_chat(bot, bot_current_stage, p) 
                            color = bot.get_color() 
                            try: 
                                asyncio.run(channel_layer.group_send(
                                    room_group,
                                    {
                                        'type': 'chat_message',
                                        'message': p,
                                        'user': bot.nickname,
                                        'color':  color,
                                        'user_id':bot.bot.id,
                                        'is_bot': True
                                        # 'user': self.user.username+'('+str(self.user.id)+')'
                                    }
                                ))
                                
                            except:                                
                                print("Exception ocurred when sending message to chat")
                                time.sleep(5)
                    

            else:
                print("Bot coin flip failed")
            self.retry(args=[data], countdown=bot.bot.poll_time)


    