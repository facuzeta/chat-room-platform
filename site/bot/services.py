import os
import logging
import requests

logger = logging.getLogger(__name__)


def _parse_response(response):
    data = response.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"].strip()
    return data["message"]["content"]


def send_message_openai_model(bot, messages):
    api_key = os.environ["OPEN_AI_API_KEY"]
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": bot.model,
        "messages": messages,
        "max_tokens": bot.max_tokens,
        "temperature": bot.temperature,
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.ok:
            return messages, _parse_response(response)
        logger.error("OpenAI error %s: %s", response.status_code, response.text)
    except Exception as e:
        logger.error("OpenAI request failed: %s", e)
    return messages, ""


def send_message_external_ollama_model(bot, messages):
    url = os.environ["EXTERNAL_OLLAMA_URL"]
    headers = {"Authorization": f"Bearer {os.environ['EXTERNAL_OLLAMA_KEY']}"}
    payload = {"model": bot.model, "messages": messages, "stream": False}
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.ok:
            return messages, _parse_response(response)
        logger.error("External Ollama error %s: %s", response.status_code, response.text)
    except Exception as e:
        logger.error("External Ollama request failed: %s", e)
    return messages, ""


def send_message_local_ollama_model(bot, messages):
    url = "http://localhost:11434/api/chat"
    payload = {"model": bot.model, "messages": messages, "stream": False}
    try:
        response = requests.post(url, json=payload)
        if response.ok:
            return messages, _parse_response(response)
        logger.error("Local Ollama error %s: %s", response.status_code, response.text)
    except Exception as e:
        logger.error("Local Ollama request failed: %s", e)
    return messages, ""
