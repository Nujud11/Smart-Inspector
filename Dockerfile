FROM python:3.11-slim

# مكتبات نظام يحتاجها OpenCV وYOLO
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face يشغل الحاوية بالمستخدم رقم 1000
RUN useradd -m -u 1000 user

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics

WORKDIR $HOME/app

# نسخ ملف المتطلبات أولًا للاستفادة من Docker cache
COPY --chown=user requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

# تثبيت نسخة CPU من PyTorch لتجنب حزم CUDA الضخمة
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch torchvision

RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية ملفات المشروع
COPY --chown=user . .

# إنشاء مجلدات الصور المؤقتة
RUN mkdir -p static/uploads static/results outputs

EXPOSE 7860

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "1", "--timeout", "300"]