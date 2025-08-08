from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import traceback

from fortune import get_fortune
from trend import extract_main_and_sub_related
from anime_search import handle_anime_search  # アニメ検索モジュール

app = Flask(__name__)

# LINE Bot API初期化
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
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

        # 流行検索開始コマンド
        elif user_msg == "流行検索":
            print("[ACTION] trend start")
            user_state[user_id] = "awaiting_keyword"
            result = "検索したい単語を入力してください（例：新潟、駅）"

        # 流行検索のキーワード入力受付中
        elif user_state.get(user_id) == "awaiting_keyword":
            print("[ACTION] trend keyword input")
            user_state[user_id] = None
            result = extract_main_and_sub_related(user_msg)

        # アニメ検索開始
        elif user_msg == "アニメ検索":
            print("[ACTION] anime search start")
            user_state[user_id] = "anime_search_waiting_for_title"
            anime_search_states[user_id] = {"titles": []}
            result = "好きなアニメを教えてください。複数入れてもOK。タイトルか「検索」と入力してください。"

        # アニメ検索のタイトル入力待ち
        elif user_state.get(user_id) == "anime_search_waiting_for_title":
            result = handle_anime_search(user_id, user_msg, anime_search_states)

        else:
            # その他のメッセージはそのまま返す
            result = f"あなたが送ったメッセージ：{event.message.text}"

        # 返信送信
        line_bot_api.reply_message(
        event.reply_token,
        messages=[{"type": "text", "text": result}]
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
