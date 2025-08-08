from flask import Flask, request, abort
from linebot.v3.messaging import Configuration, ReplyMessageRequest, TextMessage
from linebot.v3.messaging import MessagingApi, ApiClient
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os
import traceback

from fortune import get_fortune
from trend import extract_main_and_sub_related
from anime_search import handle_anime_search

app = Flask(__name__)

configuration = Configuration(token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

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
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            user_id = event.source.user_id
            user_msg = event.message.text.strip().lower()
            print(f"[RECEIVED] user_id: {user_id}, message: {user_msg}")

            if user_msg in ["今日の占い", "うらない", "占い"]:
                result = get_fortune(user_id)
            elif user_msg == "流行検索":
                user_state[user_id] = "awaiting_keyword"
                result = "検索したい単語を入力してください（例：新潟、駅）"
            elif user_state.get(user_id) == "awaiting_keyword":
                user_state[user_id] = None
                result = extract_main_and_sub_related(user_msg)
            elif user_msg == "アニメ検索":
                user_state[user_id] = "anime_search_waiting_for_title"
                anime_search_states[user_id] = {"titles": []}
                result = "好きなアニメを教えてください。複数入れてもOK。タイトルか「検索」と入力してください。"
            elif user_state.get(user_id) == "anime_search_waiting_for_title":
                result = handle_anime_search(user_id, user_msg, anime_search_states)
            else:
                result = f"あなたが送ったメッセージ：{event.message.text}"

            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=result)]
                )
            )

        except Exception as e:
            print("[ERROR in handle_message]", e)
            print(traceback.format_exc())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
