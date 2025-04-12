from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import openai
import requests
import os
from tempfile import NamedTemporaryFile
from twilio.rest import Client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CALLER_NUMBER = os.getenv("TWILIO_CALLER_NUMBER")

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

@app.post("/generate-script")
async def generate_script(data: ScriptRequest):
    full_prompt = f"Karakter adı: {data.character_name}\nKarakter tanımı: {data.character_description}\nKonuşma akışı: {data.prompt}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sen satış odaklı bir sesli asistan yazılımısın."},
            {"role": "user", "content": full_prompt}
        ]
    )
    return {"script": response.choices[0].message.content.strip()}

@app.post("/upload-customers")
async def upload_customers(file: UploadFile = File(...)):
    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    df = pd.read_excel(tmp_path)
    records = df.to_dict(orient="records")
    os.remove(tmp_path)
    return {"customers": records}

@app.post("/generate-voice")
async def generate_voice(data: VoiceRequest):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{data.voice}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": data.text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        with NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(response.content)
            return {"audio_path": f.name}
    else:
        return {"error": "Ses oluşturulamadı."}

@app.post("/start-call")
async def start_call(data: CallRequest):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        twiml=f'<Response><Play>{data.audio_url}</Play></Response>',
        to=data.to_number,
        from_=TWILIO_CALLER_NUMBER
    )
    return {"status": "calling", "sid": call.sid"}
