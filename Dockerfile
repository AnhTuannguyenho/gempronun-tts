# Kokoro TTS — RunPod Serverless LOAD BALANCER image (GPU). Flask HTTP server.
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/models \
    PIP_NO_CACHE_DIR=1 \
    PORT=80

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip ffmpeg espeak-ng libsndfile1 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# torch CUDA 12.4 (cài trước để kokoro không kéo bản khác)
RUN pip install torch --index-url https://download.pytorch.org/whl/cu124
# Kokoro + G2P tiếng Anh (misaki[en] + spacy en) + flask — đúng môi trường vast chạy tốt
RUN pip install 'numpy<2' soundfile flask 'kokoro>=0.9.4' 'misaki[en]' \
    && python -m spacy download en_core_web_sm

COPY app.py /app/

# Nướng sẵn model Kokoro 82M + vài giọng (CPU lúc build)
RUN python - <<'PY'
import os
os.environ["HF_HOME"] = "/models"
from kokoro import KPipeline
for lc in ("a", "b"):
    p = KPipeline(lang_code=lc)
    for v in (["af_heart", "am_adam"] if lc == "a" else ["bf_emma", "bm_george"]):
        list(p("hello world", voice=v))
print("kokoro cached")
PY

EXPOSE 80
CMD ["python", "-u", "app.py"]
