# Python3.9の軽量版イメージを使う
FROM python:3.9-slim

# 作業ディレクトリ（コンテナ内の作業場所）を作る＆移動する
WORKDIR /app

# 必要なファイルをコンテナにコピーする（最初はrequirements.txt）
COPY requirements.txt ./

# ライブラリをインストールする
RUN pip install --no-cache-dir -r requirements.txt

# アプリのソースコードを全部コピーする
COPY . .

# コンテナを起動したときに動くコマンド
CMD ["python", "app.py"]
