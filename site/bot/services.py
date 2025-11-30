from group_manager.models import Participant, Group,Experiment
import os 
import logging
import requests
import json

from bot.models import Argument, Bot
from django.db.models import Q

logger = logging.getLogger(__name__)

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

def send_message_openai_model(bot, messages):
        api_key = os.environ["OPEN_AI_API_KEY"]
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = { "model": bot.model, "messages" : messages ,"max_tokens": bot.max_tokens, "temperature": bot.temperature}
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
    
def send_message_external_ollama_model(bot, messages):
    key = os.environ["EXTERNAL_OLLAMA_KEY"]
    url = os.environ["EXTERNAL_OLLAMA_URL"]
    headers = {
        "Authorization": f"Bearer {key}"
    }            
    data = { "model": bot.model, "messages" : messages, "stream": False}  
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

def send_message_local_ollama_model(bot, messages):
    url = "http://localhost:11434/api/chat"
    data = { "model": bot.model, "messages" : messages, "stream": False}                 
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