FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

ENV SSL_CERT_FILE=$(python -m certifi)

COPY . .

CMD ["python", "app.py"]
