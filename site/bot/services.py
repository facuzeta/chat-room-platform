from group_manager.models import Participant, Group,Experiment
import os 
import logging
import requests
import json

from bot.models import Argument, Bot
from django.db.models import Q

logger = logging.getLogger(__name__)

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