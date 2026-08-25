import os
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from chatbot import generate_response
from pydantic import BaseModel

app = FastAPI()

# Enable CORS to allow your frontend to talk to your Vercel backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all websites (and local files) to connect
    allow_credentials=False, # STRICT RULE: Must be False when allow_origins is "*"
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- Environment Configuration for WhatsApp ---
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "1315106585012589")
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "nchs_secure_verify_token_123")

class Message(BaseModel):
    message: str

# --- Original React Frontend Chat Endpoint ---
@app.post("/chat")
async def chat_endpoint(req: Message):
    reply = generate_response(req.message)
    return {"reply": reply}

# --- 1. WhatsApp Webhook Verification Route (GET) ---
@app.get("/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge) if challenge else "OK"
    raise HTTPException(status_code=403, detail="Verification failed: Invalid verify token")

# --- 2. WhatsApp Incoming Message Receiver Webhook (POST) ---
@app.post("/whatsapp")
async def receive_whatsapp_message(request: Request):
    try:
        data = await request.json()
        
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            message = messages[0]
            from_number = message.get("from") # Student's WhatsApp phone number
            message_body = message.get("text", {}).get("body", "")

            if message_body:
                # Generate AI response using your existing chatbot logic
                bot_reply = generate_response(message_body)

                # Send response back to the user via WhatsApp API
                send_whatsapp_message(from_number, bot_reply)

    except Exception as e:
        print(f"Error handling WhatsApp message: {e}")

    return {"status": "received"}

# --- Helper to Send Message via WhatsApp Cloud API ---
def send_whatsapp_message(to_number: str, message_text: str):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"WhatsApp API Response: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")

# --- Root Endpoint ---
@app.get("/")
async def root():
    return {"status": "NCHS Chatbot Backend (FastAPI) is live and ready for WhatsApp!"}
