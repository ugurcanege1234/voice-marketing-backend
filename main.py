from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import uuid
import os

app = FastAPI()

# CORS ayarı: Frontend'ten istek gelmesini sağlar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Voice Marketing Backend aktif 🎯"}

@app.post("/upload-customers")
async def upload_customers(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_excel(contents) if file.filename.endswith('.xlsx') else pd.read_csv(contents)
    customers = df.to_dict(orient="records")
    return {"customers": customers}

@app.post("/generate-script")
async def generate_script(
    character_name: str = Form(...),
    character_description: str = Form(...),
    prompt: str = Form(...)
):
    # Buraya OpenAI ile senaryo üretme entegrasyonu gelecek
    return {"script": f"Merhaba, ben {character_name}. {prompt}"}

@app.post("/generate-voice")
async def generate_voice(text: str = Form(...), voice: str = Form(...)):
    audio_url = f"https://fake-audio.com/{uuid.uuid4()}.mp3"
    return {"audio_path": audio_url}

@app.post("/start-call")
async def start_call(to_number: str = Form(...), audio_url: str = Form(...)):
    # Buraya Twilio veya başka servis entegrasyonu gelir
    return {"status": f"Arama başlatıldı: {to_number}"}
