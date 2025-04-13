from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from twilio.rest import Client
import requests
import json
from dotenv import load_dotenv
import tempfile

# .env dosyasından çevresel değişkenleri yükle
load_dotenv()

# API anahtarlarını çevresel değişkenlerden al
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# FastAPI uygulamasını başlat
app = FastAPI(title="Sesli Pazarlama API")

# CORS ayarlarını yapılandır
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm originlere izin ver (geliştirme için)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Ana endpoint - API'nin aktif olduğunu doğrula"""
    return {"message": "Sesli Pazarlama API aktif", "status": "online"}

@app.post("/upload-customers")
async def upload_customers(file: UploadFile = File(...)):
    """Excel veya CSV dosyasından müşteri listesini yükle"""
    try:
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp:
            # Yüklenen dosyayı geçici dosyaya yaz
            content = await file.read()
            temp.write(content)
            temp_path = temp.name
        
        # Dosya formatına göre okuma işlemi
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(temp_path)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(temp_path)
        else:
            # Geçici dosyayı sil
            os.unlink(temp_path)
            raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formatı. Lütfen .xlsx, .xls veya .csv dosyası yükleyin.")
        
        # Geçici dosyayı sil
        os.unlink(temp_path)
        
        # Veri çerçevesini JSON verilerine dönüştür
        customers = df.to_dict(orient="records")
        
        # Telefon ve Ad/İsim sütunlarının varlığını kontrol et
        required_columns = ["Telefon", "Ad"]
        for column in required_columns:
            if column not in df.columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"'{column}' sütunu bulunamadı. Excel dosyanızda 'Ad' ve 'Telefon' sütunları olmalıdır."
                )
        
        return {"customers": customers, "count": len(customers)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya işlenirken hata oluştu: {str(e)}")

@app.post("/generate-script")
async def generate_script(
    character_name: str = Form(...),
    character_description: str = Form(...),
    prompt: str = Form(...)
):
    """OpenAI API kullanarak konuşma metni oluştur"""
    try:
        # API anahtarını kontrol et
        if not OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OpenAI API anahtarı bulunamadı")
        
        # OpenAI API isteği için headers
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Kullanıcı girdilerinden prompt oluştur
        full_prompt = f"""
        Karakter adı: {character_name}
        Karakter tanımı: {character_description}
        Konuşma akışı: {prompt}
        
        Bu bilgilere göre müşteriyle konuşma metni oluştur. Metin doğal ve akıcı olmalı.
        """
        
        # OpenAI API isteği için payload
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "Sen satış odaklı bir sesli asistan geliştiricisisin."},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.7
        }
        
        # OpenAI API isteğini gönder
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers, 
            json=payload
        )
        
        # API yanıtını kontrol et
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenAI API hatası: {response.text}"
            )
        
        # API yanıtını işle
        data = response.json()
        script = data["choices"][0]["message"]["content"]
        
        return {"script": script}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Konuşma metni oluşturulurken hata oluştu: {str(e)}")

@app.post("/generate-voice")
async def generate_voice(
    text: str = Form(...), 
    voice: str = Form(...)
):
    """ElevenLabs API kullanarak ses dosyası oluştur"""
    try:
        # API anahtarını kontrol et
        if not ELEVENLABS_API_KEY:
            raise HTTPException(status_code=500, detail="ElevenLabs API anahtarı bulunamadı")
        
        # Voice ID değerlerini tanımla
        voice_ids = {
            "Bella": "EXAVITQu4vr4xnSDxMaL",  # Türkçe kadın sesi
            "Clara": "21m00Tcm4TlvDq8ikWAM",  # İngilizce kadın sesi
            "Rachel": "21m00Tcm4TlvDq8ikWAM", # İngilizce kadın sesi
            "Adam": "pNInz6obpgDQGcFmaJgB",   # İngilizce erkek sesi
            "Josh": "TxGEqnHWrfWFTfGW9XjX"    # İngilizce erkek sesi
        }
        
        # Seçilen ses ID'sini al, yoksa varsayılan olarak Bella kullan
        voice_id = voice_ids.get(voice, "EXAVITQu4vr4xnSDxMaL")
        
        # ElevenLabs API isteği için URL
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        # ElevenLabs API isteği için headers
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        # ElevenLabs API isteği için payload
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        # ElevenLabs API isteğini gönder
        response = requests.post(url, json=payload, headers=headers)
        
        # API yanıtını kontrol et
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ElevenLabs API hatası: {response.text}"
            )
        
        # Ses dosyası için benzersiz isim oluştur
        voice_file_name = f"{voice}_{hash(text)}.mp3"
        
        # Ses dosyasını geçici olarak kaydet
        # Gerçek uygulamada: Burada ses dosyasını Amazon S3 veya benzeri bir depolama alanına yükleyebilirsiniz
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            temp.write(response.content)
            temp_path = temp.name
        
        # Ses dosyasının yolunu döndür
        # Gerçek uygulamada: Burada depolama alanındaki gerçek URL'yi döndürmeniz gerekir
        audio_url = f"https://example.com/audio/{voice_file_name}"
        
        # Test amaçlı geçici bir URL döndür
        return {"audio_path": audio_url, "temp_file_path": temp_path}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ses oluşturulurken hata oluştu: {str(e)}")

@app.post("/start-call")
async def start_call(
    to_number: str = Form(...), 
    audio_url: str = Form(...)
):
    """Twilio API kullanarak arama başlat"""
    try:
        # API anahtarlarını kontrol et
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            raise HTTPException(status_code=500, detail="Twilio API bilgileri eksik")
        
        # Twilio client başlat
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Arama başlat
        call = client.calls.create(
            twiml=f'<Response><Play>{audio_url}</Play></Response>',
            to=to_number,
            from_=TWILIO_PHONE_NUMBER
        )
        
        # Arama bilgilerini döndür
        return {"status": "calling", "sid": call.sid, "to": to_number}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arama başlatılırken hata oluştu: {str(e)}")

# Uvicorn ile doğrudan çalıştırmak için
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
