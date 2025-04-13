from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import pandas as pd
import os
from dotenv import load_dotenv
import requests
import uuid

load_dotenv()

app = FastAPI()

# CORS yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploaded_customers"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload-customers")
async def upload_customers(file: UploadFile = File(...)):
    contents = await file.read()
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    # Dosyayı oku
    df = pd.read_excel(filepath) if file.filename.endswith((".xlsx", ".xls")) else pd.read_csv(filepath)
    return {"customers": df.to_dict(orient="records")}

@app.post("/generate-script")
async def generate_script(
    character_name: str = Form(...),
    character_description: str = Form(...),
    prompt: str = Form(...)
):
    gpt_prompt = f"{character_name} ({character_description}) karakteriyle konuşma başlat:\n{prompt}"
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": gpt_prompt}]
        }
    )
    data = response.json()
    script = data["choices"][0]["message"]["content"]
    return {"script": script}

@app.post("/generate-voice")
async def generate_voice(text: str = Form(...), voice: str = Form(...)):
    # Bu örnekte ses üretim API'si varsayılmıştır. Gerçek bir API entegre edilecekse burada ayarlanır.
    return {"audio_path": "https://example.com/fake-audio.mp3"}

@app.post("/start-call")
async def start_call(to_number: str = Form(...), audio_url: str = Form(...)):
    # Bu örnek, Twilio üzerinden arama yapıyor.
    from twilio.rest import Client
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    call = client.calls.create(
        to=to_number,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=audio_url  # Bu gerçek TwiML ya da ses dosy_
