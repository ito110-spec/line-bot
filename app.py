from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.models import TextMessage
import os
import traceback

# 自作モジュール
from fortune import get_fortune
from trend import extract_main_and_sub_related

# Flask アプリ初期化
app = Flask(__name__)

# LINE Bot 初期化（v3）
config = Configuration(access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
line_bot_api = MessagingApi(configuration=config)
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

# ユーザー状態を保持する辞書
user_state = {}

# Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("[Webhook Error]", e)
        abort(400)

    return "OK"

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        user_id = event.source.user_id
        user_msg = event.message.text.strip().lower()
        print(f"[RECEIVED] user_id: {user_id}, message: {user_msg}")

        if user_msg in ["今日の占い", "うらない", "占い"]:
            print("[ACTION] fortune")
            result = get_fortune(user_id)

        elif user_msg == "流行検索":
            print("[ACTION] trend start")
            user_state[user_id] = "awaiting_keyword"
            result = "検索したい単語を入力してください（例：新潟、駅）"

        elif user_state.get(user_id) == "awaiting_keyword":
            print("[ACTION] trend keyword input")
            user_state[user_id] = None
            result = extract_main_and_sub_related(user_msg)

        else:
            result = f"あなたが送ったメッセージ：{event.message.text}"

        line_bot_api.reply_message(
            event.reply_token,
            messages=[TextMessage(text=result)]
        )

    except Exception as e:
        print("[ERROR in handle_message]", e)
        print(traceback.format_exc())

# SSLの証明書パス確認（Render向け）
import certifi
print("certifi cacert.pem path:", certifi.where())
print("SSL_CERT_FILE env:", os.environ.get("SSL_CERT_FILE"))

# Flask 実行
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
