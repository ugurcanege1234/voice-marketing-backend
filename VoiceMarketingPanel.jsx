
import React, { useState } from 'react';

export default function VoiceMarketingPanel() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [characterName, setCharacterName] = useState('');
  const [characterDescription, setCharacterDescription] = useState('');
  const [prompt, setPrompt] = useState('');
  const [excelFile, setExcelFile] = useState(null);
  const [voice, setVoice] = useState('Bella');
  const [response, setResponse] = useState('');

  const handleFileUpload = (e) => {
    setExcelFile(e.target.files[0]);
  };

  const handleStartCampaign = async () => {
    const formData = new FormData();
    formData.append('file', excelFile);

    const customerRes = await fetch('https://voice-marketing-backend.onrender.com/upload-customers', {
      method: 'POST',
      body: formData,
    });
    const customersData = await customerRes.json();

    const scriptRes = await fetch('https://voice-marketing-backend.onrender.com/generate-script', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        character_name: characterName,
        character_description: characterDescription,
        prompt: prompt,
      }),
    });
    const scriptData = await scriptRes.json();

    const voiceRes = await fetch('https://voice-marketing-backend.onrender.com/generate-voice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: scriptData.script,
        voice: voice,
      }),
    });
    const voiceData = await voiceRes.json();

    const results = [];
    for (const customer of customersData.customers) {
      const callRes = await fetch('https://voice-marketing-backend.onrender.com/start-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_number: customer.Telefon,
          audio_url: voiceData.audio_path,
        }),
      });
      const callResult = await callRes.json();
      results.push({ customer: customer.Ad, status: callResult.status });
    }

    setResponse(JSON.stringify(results, null, 2));
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '24px' }}>
      <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>📞 Sesli Pazarlama Paneli</h2>

      <div style={{ marginBottom: '12px' }}>
        <label>Kendi Numaranız:</label>
        <input type="text" placeholder="+90 5xx xxx xx xx" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} style={{ width: '100%', padding: '8px' }} />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>Asistan Adı:</label>
        <input type="text" placeholder="Örn: Burcu" value={characterName} onChange={(e) => setCharacterName(e.target.value)} style={{ width: '100%', padding: '8px' }} />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>Karakter Tanımı:</label>
        <textarea placeholder="Asistanın tarzı nasıl olsun?" value={characterDescription} onChange={(e) => setCharacterDescription(e.target.value)} style={{ width: '100%', padding: '8px' }} />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>Konuşma Akışı Prompt:</label>
        <textarea placeholder="GPT’ye verilecek genel konuşma yapısı" value={prompt} onChange={(e) => setPrompt(e.target.value)} style={{ width: '100%', padding: '8px' }} />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>Müşteri Excel Dosyası:</label>
        <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFileUpload} style={{ width: '100%', padding: '8px' }} />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>Ses Seçimi:</label>
        <select value={voice} onChange={(e) => setVoice(e.target.value)} style={{ width: '100%', padding: '8px' }}>
          <option value="Bella">Bella (Kadın – Samimi)</option>
          <option value="Clara">Clara (Kadın – Kurumsal)</option>
          <option value="Rachel">Rachel (Kadın – Net)</option>
          <option value="Adam">Adam (Erkek – Sakin)</option>
          <option value="Josh">Josh (Erkek – Dinamik)</option>
        </select>
      </div>

      <button onClick={handleStartCampaign} style={{ width: '100%', padding: '12px', backgroundColor: '#0070f3', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}>
        🚀 Kampanyayı Başlat
      </button>

      {response && (
        <pre style={{ marginTop: '20px', background: '#f4f4f4', padding: '16px', borderRadius: '4px' }}>{response}</pre>
      )}
    </div>
  );
}
