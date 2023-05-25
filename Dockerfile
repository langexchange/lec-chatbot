FROM bitnami/pytorch

USER root

# #ffmpeg for whisper
RUN apt update
RUN apt install -y ffmpeg

# Build app dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python","main.py","-d"]