#!/usr/bin/env python3
# Kokoro TTS — RunPod Serverless LOAD BALANCER (Flask HTTP server, không qua hàng đợi).
# /ping: 200 sẵn sàng | 204 đang nạp.  /tts: trả audio (mp3 mặc định / wav / json base64).
import base64
import os
import re
import subprocess
import tempfile
import threading
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import soundfile as sf
from flask import Flask, request, Response, jsonify

os.environ.setdefault("HF_HOME", "/models")

VOICES = ["af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky",
          "am_adam", "am_michael", "bf_emma", "bf_isabella", "bm_george", "bm_lewis"]
DEFAULT_VOICE = "af_heart"
SR = 24000

app = Flask(__name__)
_lock = threading.Lock()
_ready = False
_pipes = {}


def _pipe(lang):
    if lang not in _pipes:
        from kokoro import KPipeline
        _pipes[lang] = KPipeline(lang_code=lang)
    return _pipes[lang]


def _lang(voice):
    return 'b' if voice[:1] == 'b' else 'a'


def _synth(text, voice, speed):
    chunks = []
    with _lock:
        for _g, _p, au in _pipe(_lang(voice))(text, voice=voice, speed=speed):
            a = au.detach().cpu().numpy() if hasattr(au, "detach") else np.asarray(au)
            chunks.append(a)
    if not chunks:
        return None
    return (np.concatenate(chunks) if len(chunks) > 1 else chunks[0]).astype(np.float32)


def _load():
    global _ready
    try:
        _synth("Hello world.", DEFAULT_VOICE, 1.0)   # nạp + warm Kokoro lên GPU
        print("[tts] kokoro ready", flush=True)
    except Exception as e:
        print("[tts] load error:", e, flush=True)
    _ready = True


@app.after_request
def _cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "X-API-Key, Content-Type, Authorization"
    return r


@app.get("/ping")
def ping():
    return ("", 200) if _ready else ("", 204)


@app.get("/health")
def health():
    return jsonify(ok=_ready, engine="kokoro", voices=VOICES, default=DEFAULT_VOICE)


@app.route("/tts", methods=["GET", "POST"])
def tts():
    if not _ready:
        return jsonify(ok=False, err="model loading"), 503
    j = request.get_json(silent=True) if request.is_json else None
    src = j if j else request.values
    text = (str(src.get("text") or src.get("t") or "")).strip()[:2000]
    voice = re.sub(r"[^a-z_]", "", (str(src.get("voice") or src.get("v") or DEFAULT_VOICE)).lower()) or DEFAULT_VOICE
    if voice not in VOICES:
        voice = DEFAULT_VOICE
    fmt = (str(src.get("format") or "mp3")).lower()
    want_json = str(src.get("json") or "") in ("1", "true") or (request.headers.get("Accept", "").startswith("application/json"))
    try:
        speed = float(src.get("speed") or 1)
    except Exception:
        speed = 1.0
    if not text:
        return jsonify(ok=False, err="no text"), 400
    try:
        wav = _synth(text, voice, speed)
        if wav is None:
            return jsonify(ok=False, err="empty audio"), 500
        with tempfile.TemporaryDirectory() as d:
            wp = os.path.join(d, "a.wav")
            sf.write(wp, wav, SR, subtype="PCM_16")
            if fmt == "wav":
                data = open(wp, "rb").read(); mime = "audio/wav"
            else:
                mp = os.path.join(d, "a.mp3")
                subprocess.run(["ffmpeg", "-y", "-i", wp, "-b:a", "96k", mp], check=True, capture_output=True)
                data = open(mp, "rb").read(); mime = "audio/mpeg"; fmt = "mp3"
        if want_json:
            return jsonify(ok=True, audio_b64=base64.b64encode(data).decode(),
                           format=fmt, voice=voice, dur=round(len(wav) / SR, 2))
        return Response(data, mimetype=mime)   # mặc định: trả audio thô (dùng thẳng cho <audio>)
    except Exception as e:
        return jsonify(ok=False, err=str(e)), 500


if __name__ == "__main__":
    threading.Thread(target=_load, daemon=True).start()
    port = int(os.environ.get("PORT", "80"))
    app.run(host="0.0.0.0", port=port, threaded=True)
