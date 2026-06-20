# Kokoro TTS — RunPod Serverless (Load Balancer)

TTS đọc mẫu (Kokoro 82M). Chạy chế độ **Load Balancer** (HTTP thẳng, không qua hàng đợi).

## Tạo endpoint
Console → New Endpoint → Import Git `AnhTuannguyenho/gempronun-tts` → Advanced settings → **Load balancer** → Deploy.
GPU: chọn **Ampere/Ada** (3090/4090/A-series/L-series) — KHÔNG Blackwell (torch cu124).

## Gọi
```
POST https://<ENDPOINT_ID>.api.runpod.ai/tts
Authorization: Bearer <KEY>
Body (JSON):  {"text":"Hello world","voice":"af_heart","format":"mp3","speed":1}
hoặc form/GET: ?text=...&voice=...&format=mp3
```
- Mặc định trả **audio thô** (mp3) — dùng thẳng. Thêm `"json":1` → trả `{audio_b64}`.
- Giọng: af_heart, af_bella, am_adam, am_michael, bf_emma, bm_george... (a*=Mỹ, b*=Anh)
- `/ping` 200/204 (health), `/health` (danh sách giọng).
