FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/otaku-melons/Melon --recursive /app

RUN pip install --no-cache-dir -r requirements.txt && python main.py install -r -s

VOLUME ["/app/Configs", "/app/Logs", "/app/Output", "/app/Temp"]

ENTRYPOINT ["python", "main.py"]
