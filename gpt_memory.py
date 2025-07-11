# gpt_memory.py
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

conversations = {}

SYSTEM_PROMPT = """
You are a helpful and friendly dental clinic receptionist...
"""

def start_conversation(call_sid):
    conversations[call_sid] = [{"role": "system", "content": SYSTEM_PROMPT}]

def append_user_message(call_sid, user_text):
    conversations[call_sid].append({"role": "user", "content": user_text})

def append_assistant_message(call_sid, assistant_text):
    conversations[call_sid].append({"role": "assistant", "content": assistant_text})

def get_chatgpt_response(call_sid):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversations[call_sid],
        temperature=0.5,
    )
    return response['choices'][0]['message']['content']

def end_conversation(call_sid):
    conversations.pop(call_sid, None)
