import time
import requests
import os
import subprocess
from PIL import Image

CAT_TMP_DIR = "/tmp/cat_videos"
TMP_FRAMES_DIR = os.path.join(CAT_TMP_DIR, "tmp_frames")
os.makedirs(TMP_FRAMES_DIR, exist_ok=True)

BASE_URL = "https://line-bot-1-rsyx.onrender.com"  # ←自分の render URL に置き換える

def get_cat_video_url(max_seconds=15):
    gif_url = f"https://cataas.com/cat/gif?{int(time.time())}"
    gif_path = os.path.join(CAT_TMP_DIR, "cat.gif")
    mp4_path = os.path.join(CAT_TMP_DIR, "cat.mp4")
    preview_path = os.path.join(CAT_TMP_DIR, "preview.png")

    # GIF ダウンロード
    r = requests.get(gif_url)
    r.raise_for_status()
    with open(gif_path, "wb") as f:
        f.write(r.content)

    # プレビュー画像
    im = Image.open(gif_path)
    im.seek(0)
    im.save(preview_path)

    mp4_path_abs = os.path.abspath(mp4_path).replace("\\", "/")

    # FFmpeg で GIF → MP4（3回ループ + 無音トラック + 正方形パディング）
    subprocess.run([
        "ffmpeg", "-y",
        "-stream_loop", "2",        # GIFを3回ループ（元GIF1回 + 2回ループ）
        "-i", gif_path,             # 入力GIF
        "-vf", "scale='min(480,iw)':-2,pad=480:480:(480-iw)/2:(480-ih)/2",  # 正方形パディング
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        mp4_path_abs
    ], check=True)


    mp4_url = f"{BASE_URL}/static/cat_videos/cat.mp4"
    preview_url = f"{BASE_URL}/static/cat_videos/preview.png"
    return mp4_url, preview_url

