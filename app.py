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
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, PostbackEvent
from linebot.v3.webhook import WebhookHandler

import os
import traceback
import random
from datetime import datetime

from fortune import get_fortune
from trend import extract_main_and_sub_related
from anime_search import handle_anime_search
from cataas import get_cat_video_url
from db import init_db, save_image_from_line, get_recent_photos, like_photo, save_user

# -------------------- 初期化 --------------------
init_db()
app = Flask(__name__)

config = Configuration(access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

user_state = {}
anime_search_states = {}

# -------------------- テキストメッセージ --------------------
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
	with ApiClient(config) as client:
		messaging_api = MessagingApi(client)
		reply_messages = []

		try:
			user_id = event.source.user_id
			user_msg = event.message.text.strip().lower()
			print(f"[RECEIVED] user_id: {user_id}, message: {user_msg}")
			
			save_user(user_id)

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
					result = handle_anime_search(user_id, user_msg, anime_search_states)
					user_state[user_id] = None
					reply_messages = [TextMessage(text=result)]
				else:
					result = handle_anime_search(user_id, user_msg, anime_search_states)
					reply_messages = [TextMessage(text=result)]

			elif user_msg in ["ねこ", "猫", "cat", "にゃー", "ニャー", "🐈"]:
				try:
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
				photos = get_recent_photos(days=7)
				if not photos:
					reply_messages = [TextMessage(text="まだ写真は保存されていません。")]
				else:
					p = random.choice(photos)
					image_url = p["image_url"]

					reply_messages = [
						ImageMessage(
							original_content_url=image_url,
							preview_image_url=image_url,
							quick_reply=QuickReply(
								items=[
									QuickReplyItem(
										action=PostbackAction(
											label="👍 いいね",
											data=f"like_photo:{p['id']}"
										)
									)
								]
							)
						)
					]

			else:
				reply_messages = [TextMessage(text=f"あなたが送ったメッセージ：{event.message.text}")]

			messaging_api.reply_message_with_http_info(
				ReplyMessageRequest(reply_token=event.reply_token, messages=reply_messages)
			)

		except Exception as e:
			print("[ERROR in handle_message]", e)
			print(traceback.format_exc())

# -------------------- 画像メッセージ --------------------
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
	with ApiClient(config) as client:
		messaging_api = MessagingApi(client)
		try:
			user_id = event.source.user_id
			message_id = event.message.id

			image_url, doc_id = save_image_from_line(message_id, user_id)

			messaging_api.reply_message_with_http_info(
				ReplyMessageRequest(
					reply_token=event.reply_token,
					messages=[TextMessage(text="📸 写真を保存しました！")]
				)
			)

		except Exception as e:
			print("[ERROR in handle_image]", e)
			messaging_api.reply_message_with_http_info(
				ReplyMessageRequest(
					reply_token=event.reply_token,
					messages=[TextMessage(text="写真の保存に失敗しました…")]
				)
			)

# -------------------- いいね機能 --------------------
@handler.add(PostbackEvent)
def handle_postback(event):
	data = event.postback.data

	# 「いいね」ボタンのPostbackかチェック
	if data.startswith("like_photo:"):
		doc_id = data.split(":")[1]  # 写真のFirestoreドキュメントID
		user_id = event.source.user_id  # 押したユーザーのID

		# セッションIDを生成（1表示につき1回を保証するため）
		# UTC時刻を付加して、同じ写真でも再表示時には別セッションとして扱う
		session_id = f"{user_id}_{doc_id}_{datetime.utcnow().isoformat()}"

		try:
			# likes処理
			result = like_photo(doc_id, user_id, session_id)

			if result == "already_liked":
				# このセッションではすでにいいね済み
				reply_text = "👍 この表示ではすでにいいねしています！"
			elif result is False:
				# 写真が存在しない場合
				reply_text = "写真が見つかりませんでした。"
			else:
				# 更新後のいいね数を返す
				reply_text = f"👍 いいねしました！ 現在 {result} 件です。"

		except Exception as e:
			print("[ERROR in like_photo]", e)
			reply_text = "いいねの更新に失敗しました。"

		# LINEに返信
		with ApiClient(config) as client:
			messaging_api = MessagingApi(client)
			messaging_api.reply_message_with_http_info(
				ReplyMessageRequest(
					reply_token=event.reply_token,
					messages=[TextMessage(text=reply_text)]
				)
			)


# -------------------- Webhook --------------------
@app.route("/callback", methods=['POST'])
def callback():
	signature = request.headers.get('X-Line-Signature')
	body = request.get_data(as_text=True)
	print("[DEBUG] Webhook called. Body length:", len(body))

	try:
		handler.handle(body, signature)
	except Exception as e:
		print("[ERROR] Webhook handle error:", e)
		traceback.print_exc()
		abort(400)

	return 'OK'

# -------------------- 毎朝機能 --------------------
@app.route("/cron", methods=["GET"])
def cron_job():
	with ApiClient(config) as client:
		messaging_api = MessagingApi(client)

		# 1. 占い
		fortune = get_fortune("cron-system")
		messaging_api.push_message_with_http_info(
			PushMessageRequest(
				to="<<対象のuser_id>>",
				messages=[TextMessage(text=f"🌟今日の占い🌟\n{fortune}")]
			)
		)

		# 2. 猫
		cat_url, preview = get_cat_video_url()
		messaging_api.push_message_with_http_info(
			PushMessageRequest(
				to="<<対象のuser_id>>",
				messages=[VideoMessage(original_content_url=cat_url, preview_image_url=preview)]
			)
		)

		# 3. 写真お題（フリー文字列）
		photo_theme = "今日のお題：#青いもの を撮ってみよう📸"
		messaging_api.push_message_with_http_info(
			PushMessageRequest(
				to="<<対象のuser_id>>",
				messages=[TextMessage(text=photo_theme)]
			)
		)
		# 4. ランダム写真
		photos = get_recent_photos(days=7)
		if not photos:
			reply_messages = [TextMessage(text="まだ写真は保存されていません。")]
		else:
			p = random.choice(photos)
			image_url = p["image_url"]

			reply_messages = [
				ImageMessage(
					original_content_url=image_url,
					preview_image_url=image_url,
					quick_reply=QuickReply(
						items=[
							QuickReplyItem(
								action=PostbackAction(
									label="👍 いいね",
									data=f"like_photo:{p['id']}"
								)
							)
						]
					)
				)
			]

	return "OK"

# -------------------- 起動 --------------------
if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)
