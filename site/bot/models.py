from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
import requests
import json
from simple_history.models import HistoricalRecords
from group_manager.models import Participant, Group,Experiment
import os 
import logging
from django.db.models import Q

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
    
    empty_replies_enabled = models.BooleanField(default=True)    

    temperature = models.FloatField(default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(2.0)])
    max_tokens = models.IntegerField(default=100, validators=[MinValueValidator(0), MaxValueValidator(1000)])

    history = HistoricalRecords()
    def __str__(self): return str(self.id)+' '+self.behaviour_nickname
    
    def send_message(self, bot_participant):
        #Gets all bot_participant relevant data
        bot_nick = bot_participant.get_nickname()

        chat_history_prev, chat_history= bot_participant.get_chat_history()   

        current_stage_n = int(bot_participant.get_current_stage().name.split('_')[-1]) 
        questions = bot_participant.get_questions_order()
        
        already_debated_questions_text=[question["text"] for question in questions[:current_stage_n-1]]
        current_question = questions[current_stage_n-1]["text"]
        arguments_for_question = Argument.objects.filter(
            Q(question_id=questions[current_stage_n-1]["question_id"],bot = self) |
            Q(question_id=questions[current_stage_n-1]["question_id"], bot__isnull=True))
        remaining_time = bot_participant.get_remaining_time()
        
        experiment_context = bot_participant.group.experiment.get_context_prompt()
        
        #mock ups
        if(self.model == "mockup_repeat"):
            if len(chat_history)>0:
                last_msg = chat_history[-1]["content"]
                return [last_msg], last_msg
            return [], "hello"
             
        if (self.model == "mockup_hello"):
            if len(chat_history)>0:
                last_msg = chat_history[-1]["content"]
            return [], "hello"
        
        messages=[]

        #Creating the system prompt messages
        system_message = "INFORMATION"     
        information_lines = []
        if(self.use_all_chat_history):
            information_lines.append("INFORMATION-FINISHED_DEBATED_TOPICS: "+ str(already_debated_questions_text)) 
            messages = [{"role" : "system", "content" :"<STARTS PREVIOUS_CHAT>"}] + chat_history_prev +  [{"role" : "system", "content" : "<ENDS PREVIOUS CHAT>"}]   
        if(self.use_time_left_threshold):
            time_left_prompt = "POSITIVE"
            if(remaining_time < self.time_left_threshold):
                time_left_prompt ="NEGATIVE"
            information_lines.append("INFORMATION-TIME: " + time_left_prompt)            

        if(self.use_current_topic):           
            information_lines.append("INFORMATION-CURRENT_TOPIC: " + current_question) 

        if(self.know_own_nickname):   
            information_lines.append("INFORMATION-NAME: " + bot_nick)

        if(self.empty_replies_enabled):
            information_lines.append("INFORMATION-MESSAGE-IS-OPTIONAL: You can send an empty reply by sending <EMPTY/>")

        if(experiment_context != ""):
            information_lines.append("INFORMATION-EXPERIMENT-CONTEXT: " + experiment_context)
        
        if(self.use_defined_arguments):
            for arg in arguments_for_question:
                information_lines.append("INFORMATION-ARGUMENTS_FOR_CURRENT_TOPIC: " + arg.argument_text)
            
        
        system_message = "\n ".join(information_lines)        
        messages = messages + [{"role" : "system", "content" :system_message}] + [{"role" : "system", "content" : "<STARTS CHAT>"}] + chat_history + [{"role" : "system", "content" : "<CHAT PAUSE>"}] + [{"role" : "system", "content" : "INSTRUCTIONS: " + self.system_prompt}]
        #Send with OPENAI API
        if self.model == "gpt-4o-mini" or self.model == "gpt-4o-mini-2024-07-18":
            return self.send_message_openai_model(messages)            

        #We use "external_ollama_" in the model name to indicate we the ollama model is not hosted locally
        if "external_ollama_" in self.model:
            return self.send_message_external_ollama_model(messages)             
        
        #By default it will send to local ollama server        
        return self.send_message_local_ollama_model(messages)
    
    def send_message_openai_model(self, messages):
        api_key = os.environ["OPEN_AI_API_KEY"]
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = { "model": self.model, "messages" : messages ,"max_tokens": self.max_tokens, "temperature": self.temperature}
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                response_json = response.json()
                return messages, response_json['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Error: {response.status_code}, {response.text}")
                return messages,""                
        except Exception as e:
            logger.error(f"Error: {e}")
        return messages,""
    
    def send_message_external_ollama_model(self, messages):
        key = os.environ["EXTERNAL_OLLAMA_KEY"]
        url = os.environ["EXTERNAL_OLLAMA_URL"]
        headers = {
            "Authorization": f"Bearer {key}"
        }            
        data = { "model": self.model, "messages" : messages, "stream": False}  
        try:          
            response = requests.post(url, headers=headers, json=data)   
            if response.status_code == 200:  
                data_response = json.loads(response.text)                  
                return messages,data_response["message"]["content"]  
            else:
                logger.error(f"Error: {response.status_code}, {response.text}")
                return messages,""                
        except Exception as e:
            logger.error(f"Error: {e}")
        return messages,""
    
    def send_message_local_ollama_model(self, messages):
        url = "http://localhost:11434/api/chat"
        data = { "model": self.model, "messages" : messages, "stream": False}                 
        try:          
                response = requests.post(url, json=data)   
                if response.status_code == 200:  
                    data_response = json.loads(response.text)                  
                    return messages, data_response["message"]["content"]  
                else:
                    logger.error(f"Error: {response.status_code}, {response.text}")
                    return messages,""                
        except Exception as e:
            logger.error(f"Error: {e}")
        return messages,""
    
class Argument(models.Model):
    argument_text=models.TextField()
    question = models.ForeignKey('group_manager.Question', on_delete=models.SET_NULL, null=True)
    bot = models.ForeignKey('Bot', on_delete=models.SET_NULL, null=True, blank=True)
    history = HistoricalRecords()