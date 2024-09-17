from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
import requests
import json
from simple_history.models import HistoricalRecords
from group_manager.models import Participant
import os 
# Create your models here.
class Bot(models.Model): 
    behaviour_nickname= models.CharField(max_length=128)   
    chatroom_nickname = models.CharField(max_length=128,blank=True, null=True)
    use_random_nickname = models.BooleanField(default=True) 
    system_prompt = models.TextField() 
    reply_probability = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])    
    llmodel = models.CharField(max_length=128)
    poll_time = models.IntegerField(default=5)   
    use_own_nickname = models.BooleanField(default=True)
    use_current_topic = models.BooleanField(default=True)
    use_all_chat_history = models.BooleanField(default=False)
    use_time_left_threshold = models.BooleanField(default=False)
    time_left_threshold = models.IntegerField(default=60)
    temperature = models.FloatField(default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(2.0)])
    max_tokens = models.IntegerField(default=100, validators=[MinValueValidator(0), MaxValueValidator(1000)])

    history = HistoricalRecords()
    def send_message(self, bot_participant):
        #Gets all bot_participant relevant data
        bot_nick = bot_participant.get_nickname()

        chat_history_prev, chat_history= bot_participant.get_chat_history()   

        current_stage_n = int(bot_participant.get_current_stage().name.split('_')[-1]) 
        questions = bot_participant.get_questions_order()
        
        already_debated_questions_text=[question["text"] for question in questions[:current_stage_n-1]]
        current_question = questions[current_stage_n-1]["text"]
        remaining_time = bot_participant.get_remaining_time()
        
        #mock ups
        if(self.behaviour_nickname == "mockup_repeat"):
            if len(chat_history)>0:
                last_msg = chat_history[-1]["content"]
                return last_msg
            return "hello"
             
        if (self.behaviour_nickname == "mockup_hello"):
            return "hello"
        
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

        if(self.use_own_nickname):   
            information_lines.append("INFORMATION-NAME: " + bot_nick)         

        system_message = "\n".join(information_lines + [self.system_prompt])
        messages = messages + [{"role" : "system", "content" :system_message}] + [{"role" : "system", "content" : "<STARTS CHAT>"}] + chat_history           
        

        #Send messages to gpt model
        if self.llmodel == "gpt-4o-mini" or self.llmodel == "gpt-4o-mini-2024-07-18":
            api_key = os.environ["OPEN_AI_API_KEY"]
            url = "https://api.openai.com/v1/chat/completions"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = { "model": self.llmodel, "messages" : messages ,"max_tokens": self.max_tokens, "temperature": self.temperature}
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    response_json = response.json()
                    return response_json['choices'][0]['message']['content'].strip()
                else:
                    print(f"Error: {response.status_code}, {response.text}")
                    return ""                
            except Exception as e:
                print(f"Error: {e}")
            return ""

        #Send messages to external ollama, needs to
        if "external_ollama" in self.behaviour_nickname:  
            key = os.environ["EXTERNAL_OLLAMA_KEY"]
            url = os.environ["EXTERNAL_OLLAMA_URL"]
            headers = {
                "Authorization": f"Bearer {key}"
            }            
            data = { "model": self.llmodel, "messages" : messages, "stream": False}  
            try:          
                response = requests.post(url, headers=headers, json=data)   
                if response.status_code == 200:  
                    data_response = json.loads(response.text)                  
                    return data_response["message"]["content"]  
                else:
                    print(f"Error: {response.status_code}, {response.text}")
                    return ""
            except Exception as e:
                print(f"Error: {e}")
            return ""
                    
        
        #By default it will send to local ollama server
        url = "http://localhost:11434/api/chat"
        data = { "model": self.llmodel, "messages" : messages, "stream": False}                 
        try:          
                response = requests.post(url, json=data)   
                if response.status_code == 200:  
                    data_response = json.loads(response.text)                  
                    return data_response["message"]["content"]  
                else:
                    print(f"Error: {response.status_code}, {response.text}")
                    return ""
        except Exception as e:
            print(f"Error: {e}")
        return ""