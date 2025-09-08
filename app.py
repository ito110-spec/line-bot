# app.py
from flask import Flask, request, abort
from linebot.v3.messaging import (
    MessagingApi,
    Configuration,
    ApiClient,
    TextMessage,
    ReplyMessageRequest,
    VideoMessage,
    ImageMessage,
    QuickReply,
    QuickReplyItem,
    PostbackAction,
    PushMessageRequest,
)

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    PostbackEvent,
)

from linebot.v3.webhook import WebhookHandler

import os
import traceback
import time

from datetime import datetime, timedelta

from fortune import get_fortune
from trend import extract_main_and_sub_related
from anime_search import handle_anime_search
from cataas import get_cat_video_url
from db import SessionLocal, Photo, init_db, save_image_from_line

# アプリ起動時にDB初期化
init_db()

app = Flask(__name__)

# LINE Bot API 初期化（v3 SDK）
config = Configuration(access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))
# ローカル画像取得用
url_root = "https://99b85f2efdd5.ngrok-free.app"

user_state = {}
anime_search_states = {}



@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(config) as client:
        messaging_api = MessagingApi(client)

        reply_messages = []  # まず空で初期化

        try:
            user_id = event.source.user_id
            user_msg = event.message.text.strip().lower()
            print(f"[RECEIVED] user_id: {user_id}, message: {user_msg}")

            if user_msg in ["今日の占い", "うらない", "占い"]:
                result = get_fortune(user_id)
                reply_messages = [TextMessage(text=result)]

            elif user_msg == "流行検索":
                user_state[user_id] = "awaiting_keyword"
                reply_messages = [TextMessage(text="検索したい単語を入力してください（例：マック、新潟）")]

            elif user_state.get(user_id) == "awaiting_keyword":
                user_state[user_id] = None
                result = extract_main_and_sub_related(user_id, user_msg)
                reply_messages = [TextMessage(text=result)]

            elif user_msg == "アニメ検索":
                user_state[user_id] = "anime_search_waiting_for_title"
                anime_search_states[user_id] = {"titles": []}
                reply_messages = [TextMessage(text="好きなアニメを教えてください。複数入れてもOK。タイトルか「検索」と入力してください。")]

            elif user_state.get(user_id) == "anime_search_waiting_for_title":
                if user_msg == "検索":
                    # 検索終了
                    result = handle_anime_search(user_id, user_msg, anime_search_states)
                    user_state[user_id] = None  # 状態リセット
                    reply_messages = [TextMessage(text=result)]
                else:
                    # アニメタイトル入力中
                    result = handle_anime_search(user_id, user_msg, anime_search_states)
                    reply_messages = [TextMessage(text=result)]

            elif user_msg in ["ねこ", "猫", "cat", "にゃー", "ニャー", "🐈"]:
                try:
                    # MP4 とプレビュー画像 URL を取得
                    cat_video_url, preview_image_url = get_cat_video_url(max_seconds=10)

                    reply_messages = [
                        VideoMessage(
                            original_content_url=cat_video_url,
                            preview_image_url=preview_image_url
                        )
                    ]

                except Exception as e:
                    print("[ERROR in cat video]", e)
                    reply_messages = [TextMessage(text="ごめん、猫動画の取得に失敗したよ…")]

            elif user_msg == "ランダム写真":
                session = SessionLocal()
                one_week_ago = datetime.now() - timedelta(days=7)

                # 過去1週間に保存された写真だけ取得
                photos = session.query(Photo).filter(Photo.created_at >= one_week_ago).all()
                session.close()

                if not photos:
                    reply_messages = [TextMessage(text="まだ写真は保存されていません。")]
                else:
                    import random
                    p = random.choice(photos)
                    image_url = f"{url_root}{p.image_url}"  # HTTPS の外部アクセス URL に変換

                    reply_messages = [
                        ImageMessage(
                            original_content_url=image_url,
                            preview_image_url=image_url,
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyItem(
                                        action=PostbackAction(
                                            label="👍 いいね",
                                            data=f"like_photo:{p.id}"  # photo_id を data に渡す
                                        )
                                    )
                                ]
                            )
                        )
                    ]


            else:
                reply_messages = [TextMessage(text=f"あなたが送ったメッセージ：{event.message.text}")]

            # ★ 必ず最後に1回だけ送信
            messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=reply_messages
                )
            )

        except Exception as e:
            print("[ERROR in handle_message]", e)
            print(traceback.format_exc())

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    with ApiClient(config) as client:
        messaging_api = MessagingApi(client)
        session = SessionLocal()
        try:
            user_id = event.source.user_id
            message_id = event.message.id

            # 1. LINEから画像をDLして保存
            local_url = save_image_from_line(message_id)

            # 2. DBに保存
            new_photo = Photo(user_id=user_id, image_url=local_url)
            session.add(new_photo)
            session.commit()

            # 3. 確認メッセージ
            messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="📸 写真を保存しました！")]
                )
            )

        except Exception as e:
            session.rollback()
            print("[ERROR in handle_image]", e)
            messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="写真の保存に失敗しました…")]
                )
            )
        finally:
            session.close()

from linebot.v3.messaging import PushMessageRequest

@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    if data.startswith("like_photo:"):
        photo_id = int(data.split(":")[1])
        session = SessionLocal()
        try:
            # Session.get() を推奨
            photo = session.get(Photo, photo_id)
            if photo:
                photo.likes += 1
                session.commit()
                reply_text = f"👍 いいねしました！ 現在 {photo.likes} 件です。"

                # 投稿者に通知 (いいねした本人以外なら)
                if photo.user_id and photo.user_id != event.source.user_id:
                    with ApiClient(config) as client:
                        messaging_api = MessagingApi(client)
                        messaging_api.push_message(
                            PushMessageRequest(
                                to=photo.user_id,
                                messages=[TextMessage(text="あなたの写真にいいねが押されました！")]
                            )
                        )
            else:
                reply_text = "写真が見つかりませんでした。"
        finally:
            session.close()

        # いいねした本人への返信
        with ApiClient(config) as client:
            messaging_api = MessagingApi(client)
            messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    print("[DEBUG] Webhook called. Body length:", len(body))
    print("[DEBUG] request body:", body[:500])  # 最初の500文字だけ表示

    try:
        handler.handle(body, signature)
        print("[DEBUG] handler.handle() called successfully")
    except Exception as e:
        print("[ERROR] Webhook handle error:", e)
        traceback.print_exc()
        abort(400)

    return 'OK'



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
