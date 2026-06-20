# Gempronun TTS — RunPod Serverless image (Kokoro 82M). CHỈ TTS (không whisper/wav2vec2).
# Mirror đúng môi trường kokoro đang chạy tốt trên vast.ai (kokoro 0.9.4 + misaki[en] + spacy en, numpy<2).
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/models \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip ffmpeg espeak-ng libsndfile1 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# torch CUDA 12.4 (khớp cu124 — cài TRƯỚC để kokoro không kéo bản torch khác)
RUN pip install torch --index-url https://download.pytorch.org/whl/cu124

# Kokoro + bộ G2P tiếng Anh (misaki[en] + spacy en_core_web_sm) — đúng như vast
RUN pip install 'numpy<2' soundfile runpod 'kokoro>=0.9.4' 'misaki[en]' \
    && python -m spacy download en_core_web_sm

COPY handler.py /app/

# Nướng sẵn model Kokoro 82M + vài giọng (CPU lúc build)
RUN python - <<'PY'
import os
os.environ["HF_HOME"] = "/models"
from kokoro import KPipeline
for lc in ("a", "b"):                                  # US + UK English
    p = KPipeline(lang_code=lc)
    for v in (["af_heart", "am_adam"] if lc == "a" else ["bf_emma", "bm_george"]):
        list(p("hello world", voice=v))
print("kokoro + voices cached")
PY

CMD ["python", "-u", "handler.py"]
