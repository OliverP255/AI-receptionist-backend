import asyncio
import websockets
import os
import json
import base64
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from deepgram import Deepgram
from gpt_memory import (
    start_conversation,
    append_user_message,
    get_chatgpt_response,
    append_assistant_message,
    end_conversation,
)
PORT = int(os.environ.get("PORT", 8080))

load_dotenv()
DG_KEY = os.getenv("DEEPGRAM_API_KEY")
dg_client = Deepgram(DG_KEY)

async def handle_audio(websocket, path):
    # Get call_sid from the query string
    query = urlparse(path).query
    call_sid = parse_qs(query).get("callSid", [None])[0]

    if not call_sid:
        print("No callSid provided in WebSocket URL.")
        await websocket.close()
        return

    print(f"WebSocket connected | Call SID: {call_sid}")
    start_conversation(call_sid)

    # Connect to Deepgram live transcription
    deepgram_socket = await dg_client.transcription.live({
        "punctuate": True,
        "interim_results": False,
        "encoding": "linear16",
        "sample_rate": 8000,  # Twilio audio
        "channels": 1,
    })

    # Handle transcriptions from Deepgram
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
                    # Optional: Send reply to frontend or TTS system

            except Exception as e:
                print(f"Error processing Deepgram response: {e}")

    asyncio.create_task(receive_transcripts())

    try:
        async for message in websocket:
            data = json.loads(message)

            if data.get("event") == "media":
                # Decode base64 audio payload
                audio_b64 = data["media"]["payload"]
                audio_bytes = base64.b64decode(audio_b64)
                await deepgram_socket.send(audio_bytes)

            elif data.get("event") == "start":
                print(f"Stream started for: {call_sid}")

            elif data.get("event") == "stop":
                print(f"Stream ended for: {call_sid}")
                end_conversation(call_sid)

    except websockets.exceptions.ConnectionClosed:
        print(f"WebSocket closed unexpectedly for: {call_sid}")
    finally:
        await deepgram_socket.finish()
        print(f"Deepgram socket closed for: {call_sid}")


if __name__ == "__main__":
    import os
    start_server = websockets.serve(handle_audio, "0.0.0.0", port=PORT)
    print(f"WebSocket server running on port {PORT}")


    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
