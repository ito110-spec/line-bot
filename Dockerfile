FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

ENV SSL_CERT_FILE=/usr/local/lib/python3.9/site-packages/certifi/cacert.pem

COPY . .

CMD ["python", "app.py"]
