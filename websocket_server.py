import asyncio
import ssl
import os
import json
import base64
from urllib.parse import urlparse, parse_qs

from aiohttp import web, WSMsgType
from dotenv import load_dotenv
from deepgram import Deepgram

from gpt_memory import (
    start_conversation,
    append_user_message,
    get_chatgpt_response,
    append_assistant_message,
    end_conversation,
)

# === Config ===
PORT = 443
DOMAIN = "test.carefully-ai.com"

# Load environment variables including Deepgram key
load_dotenv()
DG_KEY = os.getenv("DEEPGRAM_API_KEY")
dg_client = Deepgram(DG_KEY)

# SSL context using your Let's Encrypt certs (adjust paths if needed)
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(
    certfile=f'/etc/letsencrypt/live/{DOMAIN}/fullchain.pem',
    keyfile=f'/etc/letsencrypt/live/{DOMAIN}/privkey.pem'
)


#Call start handler
async def call_start_handler(request):
    data = await request.post()
    call_sid = data.get("CallSid")
    if not call_sid:
        return web.Response(text="Missing CallSid", status=400)
    
    start_conversation(call_sid)
    return web.Response(text="Conversation started", status=200)

#Call message handler
async def call_message_handler(request):
    data = await request.post()
    call_sid = data.get("CallSid")
    user_text = data.get("TranscriptionText")

    if not call_sid or not user_text:
        return web.Response(text="Missing parameters", status=400)

    append_user_message(call_sid, user_text)
    assistant_reply = get_chatgpt_response(call_sid)
    append_assistant_message(call_sid, assistant_reply)

    from twilio.twiml.voice_response import VoiceResponse
    response = VoiceResponse()
    response.say(assistant_reply)

    return web.Response(text=str(response), content_type='text/xml', status=200)


#Call end handler
async def call_end_handler(request):
    data = await request.post()
    call_sid = data.get("CallSid")

    if not call_sid:
        return web.Response(text="Missing CallSid", status=400)

    end_conversation(call_sid)
    return web.Response(text="Conversation ended", status=200)




# === HTTP handler for Twilio incoming call webhook ===
async def incoming_call_handler(request):
    # Twilio expects TwiML XML instructing it to open WebSocket stream
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Start>
        <Stream url="https://{DOMAIN}/stream" />
    </Start>
    <Say>Connecting you now.</Say>
</Response>"""
    return web.Response(text=twiml, content_type='text/xml')

# === WebSocket handler for /stream ===
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Get callSid from query string
    call_sid = request.rel_url.query.get("callSid")
    if not call_sid:
        await ws.close(message=b"No callSid provided")
        return ws

    print(f"WebSocket connected | Call SID: {call_sid}")
    start_conversation(call_sid)

    # Connect to Deepgram live transcription
    deepgram_socket = await dg_client.transcription.live({
        "punctuate": True,
        "interim_results": False,
        "encoding": "linear16",
        "sample_rate": 8000,
        "channels": 1,
    })

    # Task to receive Deepgram transcripts asynchronously
    async def receive_transcripts():
        async for msg in deepgram_socket:
            try:
                msg_data = json.loads(msg)
                transcript = msg_data.get("channel", {}).get("alternatives", [{}])[0].get("transcript")
                if transcript:
                    print(f"Transcript: {transcript}")

                    append_user_message(call_sid, transcript)
                    reply = get_chatgpt_response(call_sid)
                    append_assistant_message(call_sid, reply)

                    print(f"GPT: {reply}")
                    # You could send GPT reply back over ws if you want here
            except Exception as e:
                print(f"Error processing Deepgram response: {e}")

    asyncio.create_task(receive_transcripts())

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)

                if data.get("event") == "media":
                    audio_b64 = data["media"]["payload"]
                    audio_bytes = base64.b64decode(audio_b64)
                    try:
                        await deepgram_socket.send(audio_bytes)
                    except Exception as e:
                        print(f"Error sending audio to Deepgram: {e}")

                elif data.get("event") == "start":
                    print(f"Stream started for: {call_sid}")

                elif data.get("event") == "stop":
                    print(f"Stream ended for: {call_sid}")
                    end_conversation(call_sid)

            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket connection closed with error: {ws.exception()}")

    except Exception as e:
        print(f"Exception in WebSocket handler: {e}")

    finally:
        await deepgram_socket.finish()
        print(f"Deepgram socket closed for: {call_sid}")

    return ws




# === Main app setup ===
app = web.Application()
app.router.add_post('/incoming_call', incoming_call_handler)  # Twilio webhook POST
app.router.add_get('/stream', websocket_handler)             # WebSocket endpoint
app.router.add_post('/call/start', call_start_handler)
app.router.add_post('/call/message', call_message_handler)
app.router.add_post('/call/end', call_end_handler)



if __name__ == "__main__":
    print(f"Starting server on port {PORT} with SSL...")
    web.run_app(app, port=PORT, ssl_context=ssl_context)
