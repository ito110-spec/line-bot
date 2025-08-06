from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

# ← ここで読み込み
from fortune import get_fortune

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip().lower()

    if user_msg in ["今日の占い", "うらない", "占い"]:
        user_id = event.source.user_id
        result = get_fortune(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )
    elif user_msg == "流行検索":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="検索したい単語を入力してください（例：新潟、駅）")
        )
    elif "," in user_msg or "、" in user_msg or len(user_msg) > 1:
        result = get_related_words(user_msg)
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
