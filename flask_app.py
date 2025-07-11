# flask_app.py
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
from gpt_memory import start_conversation, append_user_message, get_chatgpt_response, append_assistant_message, end_conversation
import os

PORT = int(os.environ.get("PORT", 8080))


app = Flask(__name__)



@app.route("/incoming_call", methods=["POST"])
def incoming_call():
    call_sid = request.form["CallSid"]
    print(f"📞 Incoming call: {call_sid}")

    # Start tracking the conversation
    start_conversation(call_sid)

    response = VoiceResponse()

    connect = Connect()
    connect.stream(
        url="wss://your-ngrok-url-or-server/stream",  # Replace with actual WebSocket endpoint
        track="inbound_track"
    )
    response.append(connect)

    return Response(str(response), mimetype="text/xml")

@app.route("/call/start", methods=["POST"])
def call_start():
    call_sid = request.form["CallSid"]
    start_conversation(call_sid)
    return "Conversation started", 200

@app.route("/call/message", methods=["POST"])
def call_message():
    call_sid = request.form["CallSid"]
    user_text = request.form["TranscriptionText"]

    append_user_message(call_sid, user_text)
    assistant_reply = get_chatgpt_response(call_sid)
    append_assistant_message(call_sid, assistant_reply)

    response = VoiceResponse()
    response.say(assistant_reply)

    return Response(str(response), mimetype='text/xml'), 200

@app.route("/call/end", methods=["POST"])
def call_end():
    call_sid = request.form["CallSid"]
    end_conversation(call_sid)
    return "Conversation ended", 200


def run_flask_app():
    app.run(host="0.0.0.0", PORT)


if __name__ == "__main__":
    run_flask_app()

