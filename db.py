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
cred = credentials.Certificate(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
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
def like_photo(doc_id: str, user_id: str, session_id: str):
    """
    指定された写真に「いいね」を追加する関数
    - ただし 1つの session_id に対して 1回しか押せない
    - 同じユーザーでも写真が再表示されたら（別session_idなら）再度いいね可能

    引数:
        doc_id: Firestore の写真ドキュメントID
        user_id: LINE ユーザーIDなどの識別子
        session_id: 「写真を表示した時の一意のセッションID」
    戻り値:
        - "already_liked": そのセッションで既にいいね済み
        - False: 写真が存在しない
        - int: 更新後のいいね数
    """

    # ========== 1. このセッションで既に「いいね」していないか確認 ==========
    session_ref = db.collection("likes_sessions").document(session_id)
    if session_ref.get().exists:
        # もし同じ session_id が存在したら、この表示ではもういいね済み
        return "already_liked"

    # ========== 2. 対象の写真を Firestore から取得 ==========
    doc_ref = db.collection("photos").document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        # 写真が存在しない場合は False を返す
        return False

    # ========== 3. 「いいね」数を +1 する ==========
    current_likes = doc.to_dict().get("likes", 0)  # 既存のいいね数を取得（なければ0）
    new_likes = current_likes + 1
    doc_ref.update({"likes": new_likes})  # Firestore の写真ドキュメントを更新

    # ========== 4. このセッションで「いいね」したことを記録 ==========
    # likes_sessions に {user_id, photo_id, timestamp} を保存しておく
    session_ref.set({
        "user_id": user_id,
        "photo_id": doc_id,
        "timestamp": firestore.SERVER_TIMESTAMP  # Firestore側で現在時刻を自動設定
    })

    # ========== 5. 更新後のいいね数を返す ==========
    return new_likes

# -------------------- 写真削除 --------------------
def delete_photo(doc_id: str):
    """
    Firestore の写真と Cloudinary の画像を削除する関数。
    さらに、この写真に関連する likes_sessions もすべて削除。
    """

    # ======== 1. 写真ドキュメントを取得 ========
    doc_ref = db.collection("photos").document(doc_id)
    doc = doc_ref.get()

    if doc.exists:
        # ======== 2. Cloudinary から画像を削除 ========
        url = doc.to_dict()["image_url"]
        public_id = url.split("/")[-1].split(".")[0]  # 末尾ファイル名からID取得
        cloudinary.uploader.destroy(f"linebot_photos/{public_id}")

        # ======== 3. Firestore の likes_sessions を削除 ========
        # この写真に関連する session ドキュメントを検索して削除
        sessions_ref = db.collection("likes_sessions")
        query = sessions_ref.where("photo_id", "==", doc_id).stream()
        for session_doc in query:
            session_doc.reference.delete()

        # ======== 4. Firestore の写真ドキュメントを削除 ========
        doc_ref.delete()

# -------------------- ユーザーIDを保存 --------------------
def save_user(user_id):
    doc_ref = db.collection("users").document(user_id)
    if not doc_ref.get().exists:
        doc_ref.set({
            "joined_at": firestore.SERVER_TIMESTAMP
        })
        print(f"[DB] 新しいユーザー登録: {user_id}")
    else:
        print(f"[DB] 既に登録済み: {user_id}")

# -------------------- ユーザーID一覧を取得 --------------------
def get_all_users():
    users_ref = db.collection("users").stream()
    return [doc.id for doc in users_ref] # doc.id が user_id
