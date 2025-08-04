from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

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
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    reply_msg = f"あなたが送ったメッセージ：{user_msg}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_msg)
    )

if __name__ == "__main__":
    # 0.0.0.0で起動しないとRenderからアクセスできない
    app.run(host="0.0.0.0", port=5000)

