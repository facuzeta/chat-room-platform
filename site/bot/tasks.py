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
    group = bot.group
    room_group = "chat_"+ group.name       
    channel_layer = get_channel_layer()
    #El bot se queda en s1 hasta que todos los participantes terminen las encuestas 
    try:
        if bot_current_stage.name == 's1' and group != None:
            print("Bot waiting for participants to end stage s1")    
            bot_current_stage = get_stage_and_change(bot)
            
            self.retry(args=[data], countdown=2,throw = False)        
            
        #El bot checkea el chat y responde mientras esten en stage de conversacion
        if bot_current_stage.name != 's3'and group != None:
            bot_current_stage = get_stage_and_change(bot)
            total_question = group.experiment.get_total_questions()
            s2_stages = [f"s2_{i}" for i in range(1, total_question+1)]
            if bot_current_stage.name in s2_stages:    
                                    
                if bot.bot.reply_probability > random.uniform(0, 1):
                    print("Bot coin flip success, calling response")                   
                    context, bot_response = bot.message_bot()                 
                    print("Got this response [" + bot_response + "], sending it to chat")                      
                    #Si el LLM tarda mucho en hacer la respuesta y cambia el stage, no manda el mensaje
                    stage_after_think = get_stage_and_change(bot)
                    if bot_current_stage == stage_after_think:                        
                        if bot_response != "":
                            store_bot_chat(bot, bot_current_stage, bot_response, context) 
                            color = bot.get_color() 
                            try: 
                                asyncio.run(channel_layer.group_send(
                                    room_group,
                                    {
                                        'type': 'chat_message',
                                        'message': bot_response,
                                        'user': bot.nickname,
                                        'color':  color,
                                        'user_id':bot.bot.id,
                                        'is_bot': True
                                        # 'user': self.user.username+'('+str(self.user.id)+')'
                                    }
                                ))
                                
                            except:                                
                                print("Exception ocurred when sending message to chat")
                                
                            time.sleep(2)
                        

                else:
                    print("Bot coin flip failed")                
                self.retry(args=[data], countdown=bot.bot.poll_time, throw = False)
        else:
            #Esto es para dejar al bot en ultimo stage
            get_stage_and_change(bot)
    except Exception:
              
        bot.toggle_polling()


    