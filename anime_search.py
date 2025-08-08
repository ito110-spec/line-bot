# anime_search.py

# ユーザーID別にタイトルを貯めて「検索」が来るまで待つ形を想定

def handle_anime_search(user_id, user_msg, anime_search_states):
    # user_msg はすでに小文字に変換されている想定

    state = anime_search_states.get(user_id)
    if state is None:
        # 状態がない場合は初期化（念のため）
        anime_search_states[user_id] = {"titles": []}
        state = anime_search_states[user_id]

    if user_msg == "検索":
        titles = state.get("titles", [])
        if not titles:
            return "まだアニメタイトルが入力されていません。好きなアニメを教えてください。"

        # ここでタイトルに基づくおすすめロジックを入れる（今は仮で返す）
        # 例: 「転スラ」とかにマッチしたおすすめリストを返すなど

        recommended = f"あなたが入力したタイトル: {', '.join(titles)}\nおすすめアニメは後で実装します！"

        # 状態リセット
        anime_search_states[user_id] = {"titles": []}
        return recommended

    else:
        # 「検索」以外はタイトルとして追加
        titles = state.get("titles", [])
        titles.append(user_msg)
        state["titles"] = titles
        return f"タイトル「{user_msg}」を登録しました。ほかのタイトルか「検索」と入力してください。"
