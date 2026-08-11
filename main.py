from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chatbot import generate_response
from pydantic import BaseModel

app = FastAPI()

# Enable CORS to allow your frontend (port 3000) to talk to your backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

class Message(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(req: Message):
    reply = generate_response(req.message)
    return {"reply": reply}