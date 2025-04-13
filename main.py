from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from twilio.rest import Client
from dotenv import load_dotenv
import os
import pandas as pd
import uuid

# Ortam değişkenlerini yükle (.env dosyasından)
load_dotenv()

app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twilio bilgileri (ENV’den alınmalı)
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_SID, TWILIO_AUTH)

# Geçici müşteri verisi
customer_data = []

# İstek modelleri
class ScriptRequest(BaseModel):
    character_name: str
    character_description: str
    prompt: str

class VoiceRequest(BaseModel):
    text: str
    voice: str

class CallRequest(BaseModel):
    to_number: str
    audio_url: str


@app.post("/upload-customers")
async def upload_customers(file: UploadFile = File(...)):
    global customer_data
    df = pd.read_excel(file.file)
    customer_data = df.to_dict(orient="records")
    return {"customers": customer_data}


@app.post("/generate-script")
def generate_script(data: ScriptRequest):
    script = f"Merhaba, ben {data.character_name}. {data.character_description}. {data.prompt}"
    return {"script": script}


@app.post("/generate-voice")
def generate_voice(data: VoiceRequest):
    audio_url = f"https://voice-marketing-backend.onrender.com/static/audio/{uuid.uuid4()}.mp3"
    return {"audio_path": audio_url}


@app.post("/start-call")
def start_call(data: CallRequest):
    try:
        call = client.calls.create(
            to=data.to_number,
            from_=TWILIO_FROM,
            url="https://voice-marketing-backend.onrender.com/twiml",
            method="GET",
            status_callback="https://voice-marketing-backend.onrender.com/callback",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST"
        )
        return {"status": "OK", "call_sid": call.sid}
    except Exception as e:
        return {"status": "ERROR", "detail": str(e)}


@app.get("/twiml")
def twiml():
    response = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Say voice=\"Polly.Ayda\" language=\"tr-TR\">Merhaba, bu bir test aramasıdır. Lütfen geri dönüş yapın.</Say>
</Response>"""
    return Response(content=response, media_type="application/xml")


@app.get("/")
def read_root():
    return {"message": "Voice Marketing Backend is running 🚀"}
