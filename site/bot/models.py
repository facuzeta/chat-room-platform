from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
import requests
import json
from simple_history.models import HistoricalRecords
from group_manager.models import Participant, Group,Experiment
import os 
import logging
from django.db.models import Q
from bot.services import *

logger = logging.getLogger(__name__)
# Create your models here.
class Bot(models.Model): 
    #Behaviour nickname is shown to the manager when creating groups, chatroom nickname is shown in the chat.
    behaviour_nickname= models.CharField(max_length=128)    
    chatroom_nickname = models.CharField(max_length=128,blank=True, null=True)
    make_random_nickname_on_create = models.BooleanField(default=True) 

    system_prompt = models.TextField()
    model = models.CharField(max_length=128)

    reply_probability = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])    
    poll_time = models.IntegerField(default=5)   

    #If true, the bot nickname is informed of his own nickname
    know_own_nickname = models.BooleanField(default=True)

    use_current_topic = models.BooleanField(default=True)

    #If true, the bot will use the full chat history, otherwise only the messages of the current topic
    use_all_chat_history = models.BooleanField(default=False)

    #If use_time_left_threshold is true, the bot is informed if the time remaining is less than the threshold
    use_time_left_threshold = models.BooleanField(default=False)
    time_left_threshold = models.IntegerField(default=60)

    use_defined_arguments = models.BooleanField(default=True)

    wait_reply_to_generate_again = models.BooleanField(default=True)

    send_message_if_chat_inactive = models.BooleanField(default=True)
    time_chat_inactivity = models.IntegerField(default=60)
    chat_inactive_message_prompt = models.TextField(default="")

    empty_replies_enabled = models.BooleanField(default=True)    

    temperature = models.FloatField(default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(2.0)])
    max_tokens = models.IntegerField(default=100, validators=[MinValueValidator(0), MaxValueValidator(1000)])

    history = HistoricalRecords()
    
    def __str__(self): return str(self.id)+' '+self.behaviour_nickname
    def send_message(bot, bot_participant):
        #Gets all bot_participant relevant data
        bot_nick = bot_participant.get_nickname()

        chat_history_prev, chat_history, last_message_difference_in_seconds= bot_participant.get_chat_history()   

        current_stage_n = int(bot_participant.get_current_stage().name.split('_')[-1]) 
        questions = bot_participant.get_questions_order()
        
        already_debated_questions_text=[question["text"] for question in questions[:current_stage_n-1]]
        current_question = questions[current_stage_n-1]["text"]
        arguments_for_question = Argument.objects.filter(
            Q(question_id=questions[current_stage_n-1]["question_id"],bot = bot) |
            Q(question_id=questions[current_stage_n-1]["question_id"], bot__isnull=True))
        remaining_time = bot_participant.get_remaining_time()

        bot_group = bot_participant.group
        
        experiment_context = bot_group.experiment.get_context_prompt()

        participants_in_group = bot_group.get_all_user_participants()
        everyone_talked = all_participants_talked(chat_history, participants_in_group)

        chat_inactive = last_message_difference_in_seconds > bot.time_chat_inactivity and bot.send_message_if_chat_inactive
        #Don't generate two replies consecutively, if chat was inactive it generates reply anyways
        #last_message_was_sent_by_assistant = (len(chat_history) > 0) and chat_history[-1]["role"] == "assistant"
        if bot.wait_reply_to_generate_again and not(everyone_talked) and not chat_inactive:
            return [], ""       
        
        #mock ups
        if(bot.model == "mockup_repeat"):
            if len(chat_history)>0:
                last_msg = chat_history[-1]["content"]
                return [last_msg], last_msg
            return [], "hello"
             
        if (bot.model == "mockup_hello"):
            if len(chat_history)>0:
                last_msg = chat_history[-1]["content"]
            return [], "hello"
        
        messages=[]

        #Creating the system prompt messages
        system_message = "INFORMATION"     
        information_lines = []
        if(bot.use_all_chat_history):
            information_lines.append("INFORMATION-FINISHED_DEBATED_TOPICS: "+ str(already_debated_questions_text)) 
            messages = [{"role" : "system", "content" :"<STARTS PREVIOUS_CHAT>"}] + chat_history_prev +  [{"role" : "system", "content" : "<ENDS PREVIOUS CHAT>"}]   
        if(bot.use_time_left_threshold):
            time_left_prompt = "POSITIVE"
            if(remaining_time < bot.time_left_threshold):
                time_left_prompt ="NEGATIVE"
            information_lines.append("INFORMATION-TIME: " + time_left_prompt)            

        if(bot.use_current_topic):           
            information_lines.append("INFORMATION-CURRENT_TOPIC: " + current_question) 

        if(bot.know_own_nickname):   
            information_lines.append("INFORMATION-NAME: " + bot_nick)

        if(bot.empty_replies_enabled):
            information_lines.append("INFORMATION-MESSAGE-IS-OPTIONAL: You can send an empty reply by sending <EMPTY/>")

        if(experiment_context != ""):
            information_lines.append("INFORMATION-EXPERIMENT-CONTEXT: " + experiment_context)
        
        if(bot.use_defined_arguments and bot.use_current_topic):
            for arg in arguments_for_question:
                information_lines.append("INFORMATION-ARGUMENTS_FOR_CURRENT_TOPIC: " + arg.argument_text)
            
        
        system_message = "\n ".join(information_lines)        
        messages = messages + [{"role" : "system", "content" :system_message}] + [{"role" : "system", "content" : "INSTRUCTIONS: " + bot.system_prompt}] + [{"role" : "system", "content" : "<STARTS CHAT>"}] + chat_history
        
        #If chat is inactive we add a message to reactivate chat
        if chat_inactive and bot.chat_inactive_message_prompt != "":
            messages = messages + [{"role" : "system", "content" : bot.chat_inactive_message_prompt}]

        #Send with OPENAI API
        if bot.model == "gpt-4o-mini" or bot.model == "gpt-4o-mini-2024-07-18":
            return send_message_openai_model(bot, messages)            

        #We use "external_ollama_" in the model name to indicate we the ollama model is not hosted locally
        if "external_ollama_" in bot.model:
            return send_message_external_ollama_model(bot, messages)             
        
        #By default it will send to local ollama server        
        return send_message_local_ollama_model(bot, messages)
    
    
class Argument(models.Model):
    argument_text=models.TextField()
    question = models.ForeignKey('group_manager.Question', on_delete=models.SET_NULL, null=True)
    bot = models.ForeignKey('Bot', on_delete=models.SET_NULL, null=True, blank=True)
    history = HistoricalRecords()



def all_participants_talked(chat_history, participants_in_group):
    """
    chat_history: list of dicts like {"role": "user", "content": "...", "participant": participant_obj}
    participants_in_group: queryset or iterable of Participant objects
    """
    # Convert participants_in_group to a set of participant IDs (or objects if hashable)
    group_participants = set(participants_in_group)

    # Find the last assistant message index
    last_assistant_index = None
    for i in range(len(chat_history) - 1, -1, -1):
        if chat_history[i]["role"] == "assistant":
            last_assistant_index = i
            break

    if last_assistant_index is None:
        # No assistant message found → return False (or True depending on your logic)
        return False

    # Collect participants who talked after the last assistant
    talked_after_assistant = set()
    for msg in chat_history[last_assistant_index + 1:]:
        if msg["role"] == "user":
            talked_after_assistant.add(msg["participant"])

    # Check if all group participants are in talked_after_assistant
    return talked_after_assistant == group_participants