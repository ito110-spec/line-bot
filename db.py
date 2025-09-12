# db.py
import os
import requests
from datetime import datetime, timedelta
import cloudinary
import cloudinary.uploader
import firebase_admin
from firebase_admin import credentials, firestore

# -------------------- Cloudinary 初期化 --------------------
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# -------------------- Firebase 初期化 --------------------
cred = credentials.Certificate(os.environ.get("FIREBASE_CREDENTIALS"))
firebase_admin.initialize_app(cred)
db = firestore.client()

def init_db():
    # Firestore は動的作成なので何もしなくてOK
    print("Firestore ready. No DB init required.")

# -------------------- 画像保存 --------------------
def save_image_from_line(message_id: str, user_id: str):
    """
    LINE から画像を取得して Cloudinary にアップロード
    Firestore に URL を保存
    """
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise ValueError(f"LINE 画像取得失敗: {r.status_code}")

    # Cloudinary にアップロード
    result = cloudinary.uploader.upload(
        r.content,
        folder="linebot_photos",
        public_id=message_id
    )
    image_url = result["secure_url"]

    # Firestore に保存
    doc_ref = db.collection("photos").document()
    doc_ref.set({
        "user_id": user_id,
        "image_url": image_url,
        "likes": 0,
        "created_at": datetime.utcnow()
    })

    return image_url, doc_ref.id

# -------------------- 過去 N 日の写真取得 --------------------
def get_recent_photos(days=7):
    one_week_ago = datetime.utcnow() - timedelta(days=days)
    docs = db.collection("photos").where("created_at", ">=", one_week_ago).stream()
    return [doc.to_dict() | {"id": doc.id} for doc in docs]

# -------------------- いいね機能 --------------------
def like_photo(doc_id: str):
    doc_ref = db.collection("photos").document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        return False
    new_likes = doc.to_dict().get("likes", 0) + 1
    doc_ref.update({"likes": new_likes})
    return new_likes

# -------------------- 写真削除 --------------------
def delete_photo(doc_id: str):
    doc_ref = db.collection("photos").document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        # Cloudinary は public_id で削除
        url = doc.to_dict()["image_url"]
        public_id = url.split("/")[-1].split(".")[0]  # 末尾ファイル名からID取得
        cloudinary.uploader.destroy(f"linebot_photos/{public_id}")
        # Firestore 削除
        doc_ref.delete()
