# db.py
from linebot.v3.webhooks import ImageMessageContent
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
import requests

DATABASE_URL = "sqlite:///photos.db"
UPLOAD_DIR = "static/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()




class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    image_url = Column(String, index=True)
    likes = Column(Integer, default=0)  # 追加
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)

def save_image_from_line(message_id: str):
    """
    LINE APIから画像をダウンロードしてローカルに保存
    戻り値: 保存した画像の相対パス
    """
    channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {channel_access_token}"
    }
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    r = requests.get(url, headers=headers, stream=True)
    if r.status_code != 200:
        raise ValueError(f"画像取得失敗: {r.status_code}")

    filename = f"{message_id}.jpg"  # GIFでもpngでもOK
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
    return f"/{file_path.replace(os.sep, '/')}"

def delete_photo(photo_id: int):
    session = SessionLocal()
    photo = session.query(Photo).filter(Photo.id == photo_id).first()
    if photo:
        # 画像ファイル削除
        file_path = photo.image_url.lstrip("/")  # "/static/uploads/xxx.jpg" → "static/uploads/xxx.jpg"
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        
        # DB からも削除
        session.delete(photo)
        session.commit()
        print(f"Deleted DB record for photo_id={photo_id}")
    session.close()

# ✅ 確認用
if __name__ == "__main__":
    # ここでテーブルを作る
    init_db()

    session = SessionLocal()
    photos = session.query(Photo).all()
    print("=== 保存されている写真一覧 ===")
    for p in photos:
        print(f"[{p.id}] user_id={p.user_id}, url={p.image_url}, created_at={p.created_at}")
    if not photos:
        print("まだ写真は保存されていません。")
    session.close()
