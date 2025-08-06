# fortune.py
import hashlib
import datetime
from datetime import datetime, timedelta, timezone

# 各カテゴリのリスト
general_fortunes = [
    "🌞 チャンスの多い一日！やるなら今日！",
    "🌤 落ち着いていけば大丈夫。焦らず◎",
    "☁ 少し不安定。人と比べずマイペースで。",
    "🌧 無理せず休んで吉。自分に優しく。",
    "🌈 意外なところに運がある予感…！"
]

lucky_items = [
    "赤いペン", "スマホスタンド", "缶コーヒー", "折りたたみ傘", "お気に入りのアプリ"
]

lucky_colors = [
    "ブルー", "グリーン", "イエロー", "オレンジ", "ピンク"
]

quotes = [
    "焦らずゆっくり、自分のペースでOK。",
    "笑顔は最高の魔法。",
    "小さな努力が未来を変える。",
    "他人の評価より、自分の気持ちを大切に。",
    "今あるものに感謝しよう。"
]

def pick_from_list(user_id, today_str, data_list, tag):
    key = f"{user_id}_{today_str}_{tag}"
    hash_value = hashlib.sha256(key.encode()).hexdigest()
    number = int(hash_value, 16)
    index = number % len(data_list)
    return data_list[index]

def get_fortune(user_id):
    JST = timezone(timedelta(hours=9))
    now_jst = datetime.now(JST)

    # ここで日付や時間を使った処理を行う
    today_str = now_jst.strftime('%Y-%m-%d')

    general = pick_from_list(user_id, today_str, general_fortunes, "general")
    item = pick_from_list(user_id, today_str, lucky_items, "item")
    color = pick_from_list(user_id, today_str, lucky_colors, "color")
    quote = pick_from_list(user_id, today_str, quotes, "quote")

    return f"""🔮 今日の占い 🔮
🧭 総合運：{general}
🎁 ﾗｯｷｰｱｲﾃﾑ：{item}
🎨 ﾗｯｷｰｶﾗｰ：{color}
💬 今日の一言：
「{quote}」
"""
