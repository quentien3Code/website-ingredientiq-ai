# Dockerfile — CUDA 12.6 base, Python 3.8, PyTorch cu126 wheels installed
FROM nvidia/cuda:12.6.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# --- system deps + add deadsnakes for python3.8 ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common ca-certificates wget curl gnupg2 \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       python3.8 python3.8-venv python3.8-dev python3-pip \
       build-essential gcc g++ cmake git pkg-config \
       libffi-dev libssl-dev libbz2-dev zlib1g-dev liblzma-dev \
       libjpeg-dev libpng-dev libtiff5-dev libgl1-mesa-glx libglib2.0-0 \
       libsm6 libxext6 libxrender-dev tesseract-ocr libleptonica-dev libtesseract-dev \
       libsndfile1 libxml2-dev libxslt1-dev \
       && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- virtualenv (optional but keeps PATH consistent) ---
RUN python3.8 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements early for Docker cache
COPY requirements.txt /app/requirements.txt

# Install PyTorch wheels for cu126 (must match CUDA version)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu126 \
    torch==2.8.0+cu126 torchvision==0.19.0+cu126 torchaudio==2.4.0 || \
    pip install --no-cache-dir torch torchvision torchaudio

# Install remaining Python deps (requirements.txt should NOT contain torch/vision/audio)
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application and collect static files
COPY . /app

# Set environment variables for static files
ENV DJANGO_SETTINGS_MODULE=foodanalysis.settings
ENV PYTHONPATH=/app

# Collect static files with proper settings
RUN python manage.py collectstatic --noinput --clear

# Create symbolic links for React build files to handle hash changes
RUN if [ -d "/app/build/static" ]; then \
    cp -r /app/build/static/* /app/staticfiles/ && \
    find /app/staticfiles -name "main.*.css" -exec ln -sf {} /app/staticfiles/css/main.f056d19f.css \; && \
    find /app/staticfiles -name "main.*.js" -exec ln -sf {} /app/staticfiles/js/main.b538225d.js \; ; \
fi

EXPOSE 8018
CMD ["gunicorn", "--timeout", "120", "--bind", "0.0.0.0:8018", "foodanalysis.wsgi:application"]
