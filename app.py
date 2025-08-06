from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

# ← ここで読み込み
from fortune import get_fortune
from trend import handle_trend_search

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except:
        abort(400)

    return "OK"

user_state = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text.strip().lower()

    if user_msg in ["今日の占い", "うらない", "占い"]:
        result = get_fortune(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )

    elif user_msg == "流行検索":
        user_state[user_id] = "awaiting_keyword"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="検索したい単語を入力してください（例：新潟、駅）")
        )

    elif user_state.get(user_id) == "awaiting_keyword":
        user_state[user_id] = None  # 状態リセット
        result = handle_trend_search(user_id, user_msg)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )

    else:
        reply_msg = f"あなたが送ったメッセージ：{event.message.text}"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg)
        )
######################
import certifi
import os

print("certifi cacert.pem path:", certifi.where())
print("SSL_CERT_FILE env:", os.environ.get("SSL_CERT_FILE"))
######################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
