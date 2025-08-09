FROM python:3.9-slim

WORKDIR /app

# MeCab本体と辞書のインストールを追加
RUN apt-get update && apt-get install -y mecab libmecab-dev curl xz-utils file && \
    curl -L -o /tmp/mecab-ipadic.tar.gz "https://github.com/taku910/mecab/releases/download/v0.996/mecab-ipadic-2.7.0-20070801.tar.gz" && \
    mkdir -p /usr/local/lib/mecab/dic && \
    tar zxvf /tmp/mecab-ipadic.tar.gz -C /tmp && \
    cd /tmp/mecab-ipadic-* && ./configure --prefix=/usr/local/lib/mecab/dic/ipadic && make && make install && \
    rm -rf /tmp/mecab-ipadic*


COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

ENV SSL_CERT_FILE=/usr/local/lib/python3.9/site-packages/certifi/cacert.pem

COPY . .

CMD ["python", "-u", "app.py"]
