# anime_search.py

user_title_buffer = {}  # user_id → タイトルのリスト

def start_anime_search(user_id):
    """検索モードに入ったとき呼ばれる"""
    user_title_buffer[user_id] = []
    return "好きなアニメタイトルか「検索」と入力してください"

def handle_anime_input(user_id, user_input):
    """ユーザーがタイトル or 検索と入力したとき"""
    if user_id not in user_title_buffer:
        return "まず「アニメ検索」と入力してください"

    if user_input.strip() == "検索":
        titles = user_title_buffer.get(user_id, [])
        if not titles:
            return "アニメタイトルが一つも入力されていません。"
        del user_title_buffer[user_id]
        return search_recommendations(titles)

    user_title_buffer[user_id].append(user_input.strip())
    return "好きなアニメタイトルか「検索」と入力してください"

def search_recommendations(titles):
    """おすすめアニメを返す（仮のロジック）"""
    # ここにAniList APIを使った処理をあとで入れる
    titles_str = "、".join(titles)
    return f"おすすめを探しています（今は仮機能）\nあなたの好きなアニメ: {titles_str}"
