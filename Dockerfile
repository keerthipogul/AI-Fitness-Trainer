
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY main.py pose_detector.py app.py ./
COPY squat.mp4 squat1.mp4 pullups.mp4 ./

RUN pip install --no-cache-dir \
    --retries 10 \
    --timeout 120 \
    "numpy<2" \
    "mediapipe==0.10.21" \
    "opencv-python-headless==4.11.0.86" \
    "streamlit==1.45.1"

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
