from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

#################
#占い用追記
import hashlib
import datetime

fortune_list = [
    "🌞 チャンスの多い一日！やるなら今日！",
    "🌤 落ち着いていけば大丈夫。焦らず◎",
    "☁ 少し不安定。人と比べずマイペースで。",
    "🌧 無理せず休んで吉。自分に優しく。",
    "🌈 意外なところに運がある予感…！"
]

def get_fortune(user_id):
    today = datetime.date.today().isoformat()
    key = user_id + today
    hash_value = hashlib.sha256(key.encode()).hexdigest()
    number = int(hash_value, 16)
    index = number % len(fortune_list)
    return fortune_list[index]
#################

app = Flask(__name__)

# 環境変数からトークンとシークレットを取得
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

# メッセージイベント受信時の処理
#################
#占い用変更済み
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.lower()

    if user_msg in ["今日の占い", "うらない", "占い"]:
        user_id = event.source.user_id
        result = get_fortune(user_id)
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

#################

if __name__ == "__main__":
    # 0.0.0.0で起動しないとRenderからアクセスできない
    app.run(host="0.0.0.0", port=5000)

