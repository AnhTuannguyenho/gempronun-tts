# Gempronun TTS — RunPod Serverless (Kokoro)

Endpoint TTS **RIÊNG** (tách khỏi engine chấm phát âm để không gây xung đột thư viện).
Kokoro 82M (StyleTTS2), tiếng Anh Mỹ/Anh, trả mp3/wav base64.

## Gọi
```
POST https://api.runpod.ai/v2/<TTS_ENDPOINT_ID>/runsync
Authorization: Bearer <RUNPOD_API_KEY>
Content-Type: application/json
Body: {"input":{"route":"tts","text":"Hello world","voice":"af_heart","format":"mp3","speed":1}}
```
Output: `{"ok":true,"audio_b64":"<base64>","format":"mp3","voice":"af_heart","dur":1.2}`
- `voice`: af_heart, af_bella, af_nicole, af_sarah, af_sky, am_adam, am_michael, bf_emma, bf_isabella, bm_george, bm_lewis (a*=Mỹ, b*=Anh; *f*=nữ, *m*=nam)
- `format`: mp3 (mặc định) | wav · `speed`: 0.5–2 · `route":"health"` → danh sách giọng

## Triển khai
Tạo endpoint RunPod mới từ repo này (Dockerfile ở gốc). Cấu hình: GPU 16GB+ là đủ, workersMin 0, FlashBoot bật. Model nướng sẵn trong image.
