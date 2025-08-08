from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import TextMessage, ReplyMessageRequest
import os
import traceback

from fortune import get_fortune
from trend import extract_main_and_sub_related
from anime_search import handle_anime_search  # アニメ検索モジュール

app = Flask(__name__)

# LINE Bot API初期化（v3 SDK）
config = Configuration(access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
line_bot_api = MessagingApi(config)
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

# ユーザーごとの状態管理用辞書
user_state = {}
anime_search_states = {}

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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        user_id = event.source.user_id
        user_msg = event.message.text.strip().lower()
        print(f"[RECEIVED] user_id: {user_id}, message: {user_msg}")

        # 占いコマンド
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

        elif user_msg == "アニメ検索":
            print("[ACTION] anime search start")
            user_state[user_id] = "anime_search_waiting_for_title"
            anime_search_states[user_id] = {"titles": []}
            result = "好きなアニメを教えてください。複数入れてもOK。タイトルか「検索」と入力してください。"

        elif user_state.get(user_id) == "anime_search_waiting_for_title":
            result = handle_anime_search(user_id, user_msg, anime_search_states)

        else:
            result = f"あなたが送ったメッセージ：{event.message.text}"

        # ✅ 正しい返信方法（v3）
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=result)]
            )
        )

    except Exception as e:
        print("[ERROR in handle_message]", e)
        print(traceback.format_exc())

# SSL証明書パスの確認（デバッグ用）
import certifi
print("certifi cacert.pem path:", certifi.where())
print("SSL_CERT_FILE env:", os.environ.get("SSL_CERT_FILE"))

if __name__ == "__main__":
    # ポートやデバッグモードは環境に合わせて変更可能
    app.run(host="0.0.0.0", port=5000, debug=False)
