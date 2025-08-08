import requests
from collections import defaultdict

# ユーザーごとにアニメタイトルを保持する辞書
user_anime_keywords = defaultdict(list)

def reset_user_keywords(user_id):
    user_anime_keywords[user_id] = []

def add_anime_keyword(user_id, keyword):
    user_anime_keywords[user_id].append(keyword)

def fetch_recommendations(anime_titles):
    # 今回はAPI連携が未実装のため、ダミーのレコメンドを返す
    # 実際には AniList API を使用する
    dummy_db = {
        "ガンダム": ["コードギアス", "マクロス", "エウレカセブン"],
        "転スラ": ["このすば", "オーバーロード", "リゼロ"],
    }

    result_set = set()
    for title in anime_titles:
        result_set.update(dummy_db.get(title, []))

    if not result_set:
        return "おすすめのアニメが見つかりませんでした。"

    return "おすすめアニメ:\n- " + "\n- ".join(result_set)

def handle_anime_search(user_id, user_input):
    user_input = user_input.strip()

    if user_input == "検索":
        anime_titles = user_anime_keywords[user_id]
        reset_user_keywords(user_id)

        if not anime_titles:
            return "アニメタイトルが登録されていません。最初にタイトルを教えてください。"

        return fetch_recommendations(anime_titles)

    else:
        add_anime_keyword(user_id, user_input)
        return f"「{user_input}」を記録しました。続けて入力するか「検索」と送ってください。"
