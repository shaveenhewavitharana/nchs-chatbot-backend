from fastapi import FastAPI

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



class Message(BaseModel):

    message: str



@app.post("/chat")

async def chat_endpoint(req: Message):

    reply = generate_response(req.message)

    return {"reply": reply}
