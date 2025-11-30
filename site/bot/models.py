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
    
    
class Argument(models.Model):
    argument_text=models.TextField()
    question = models.ForeignKey('group_manager.Question', on_delete=models.SET_NULL, null=True)
    bot = models.ForeignKey('Bot', on_delete=models.SET_NULL, null=True, blank=True)
    history = HistoricalRecords()