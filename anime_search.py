import requests
from janome.tokenizer import Tokenizer
import os

HUGGINGFACE_API_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-rw-1b"  # 軽量モデル

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"
}

def query_huggingface(prompt):

    #テスト用
    print(f"DEBUG TOKEN: {HUGGINGFACE_API_TOKEN}")
    
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 300}
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")
    if response.status_code == 200:
        data = response.json()
        return data[0]["generated_text"] if isinstance(data, list) else data.get("generated_text", "")
    else:
        return None


def extract_keywords(text):
    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(text)
    keywords = []
    for token in tokens:
        part = token.part_of_speech.split(',')[0]
        if part in ["名詞", "形容詞"]:
            keywords.append(token.base_form)
    # 重複除去して返す
    return list(set(keywords))

def handle_anime_search(user_id, user_msg, anime_search_states):
    user_msg = user_msg.lower()
    state = anime_search_states.get(user_id)
    if state is None:
        anime_search_states[user_id] = {"titles": []}
        state = anime_search_states[user_id]

    if user_msg == "検索":
        titles = state.get("titles", [])
        if not titles:
            return "まだアニメタイトルが入力されていません。好きなアニメを教えてください。"

        # プロンプト作成
        prompt = (
            f"以下のアニメタイトルについて、それぞれのストーリーの特徴を4つのカテゴリで2つずつ挙げてください。\n"
            f"カテゴリ: 感情要素, ストーリー展開要素, 登場キャラ内面/心理要素, 世界観要素\n"
            f"タイトル一覧: {', '.join(titles)}\n"
            "回答はカテゴリごとに箇条書きで簡潔に。"
        )

        result = query_huggingface(prompt)
        if not result:
            return "おすすめを取得中にエラーが発生しました。もう一度やり直してください。"

        keywords = extract_keywords(result)

        # 状態リセット
        anime_search_states[user_id] = {"titles": []}

        return f"おすすめ生成結果:\n{result}\n\n抽出タグ:\n{', '.join(keywords)}\n"

    else:
        titles = state.get("titles", [])
        titles.append(user_msg)
        state["titles"] = titles
        return f"タイトル「{user_msg}」を登録しました。ほかのタイトルか「検索」と入力してください。"
