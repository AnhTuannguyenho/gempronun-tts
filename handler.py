#!/usr/bin/env python3
# Gempronun TTS — RunPod Serverless (Kokoro). CHỈ TTS, không dính engine chấm.
# Input job: {"input":{"route":"tts","text":"...","voice":"af_heart","lang":"a","speed":1,"format":"mp3"}}
#   route="health" -> trả danh sách giọng.
# Output: {"ok":true,"audio_b64":<base64>,"format":"mp3|wav","voice","dur"}
import base64, os, re, subprocess, tempfile, threading, warnings
warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf
import runpod

os.environ.setdefault("HF_HOME", "/models")

# a*=American, b*=British ; *f*=nữ, *m*=nam
VOICES = ["af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky",
          "am_adam", "am_michael", "bf_emma", "bf_isabella", "bm_george", "bm_lewis"]
DEFAULT_VOICE = "af_heart"
SR = 24000

_lock = threading.Lock()
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


def handler(job):
    inp = job.get("input") or {}
    if (inp.get("route") or "tts") == "health":
        return {"ok": True, "engine": "kokoro", "voices": VOICES, "default": DEFAULT_VOICE}
    text = (str(inp.get("text") or "")).strip()[:2000]
    voice = re.sub(r"[^a-z_]", "", (str(inp.get("voice") or DEFAULT_VOICE)).lower()) or DEFAULT_VOICE
    if voice not in VOICES:
        voice = DEFAULT_VOICE
    fmt = (str(inp.get("format") or "mp3")).lower()
    try:
        speed = float(inp.get("speed") or 1)
    except Exception:
        speed = 1.0
    if not text:
        return {"ok": False, "err": "no text"}
    try:
        wav = _synth(text, voice, speed)
        if wav is None:
            return {"ok": False, "err": "empty audio"}
        with tempfile.TemporaryDirectory() as d:
            wp = os.path.join(d, "a.wav")
            sf.write(wp, wav, SR, subtype="PCM_16")
            if fmt == "wav":
                data = open(wp, "rb").read(); out = "wav"
            else:
                mp = os.path.join(d, "a.mp3")
                subprocess.run(["ffmpeg", "-y", "-i", wp, "-b:a", "96k", mp], check=True, capture_output=True)
                data = open(mp, "rb").read(); out = "mp3"
        return {"ok": True, "audio_b64": base64.b64encode(data).decode(),
                "format": out, "voice": voice, "dur": round(len(wav) / SR, 2)}
    except Exception as e:
        return {"ok": False, "err": str(e)}


def _warm():
    try:
        _synth("Hello world.", DEFAULT_VOICE, 1.0)
        print("[tts] kokoro warmed (GPU ready)", flush=True)
    except Exception as e:
        print("[tts] warm skipped:", e, flush=True)


if __name__ == "__main__":
    _warm()
    runpod.serverless.start({"handler": handler})
