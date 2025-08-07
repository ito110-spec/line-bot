from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import traceback

# ← ここで読み込み
from fortune import get_fortune
from trend import extract_main_and_sub_related

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
            TextSendMessage(text=result)
        )

    except Exception as e:
        print("[ERROR in handle_message]", e)
        print(traceback.format_exc())


######################
import certifi
import os

print("certifi cacert.pem path:", certifi.where())
print("SSL_CERT_FILE env:", os.environ.get("SSL_CERT_FILE"))
######################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
