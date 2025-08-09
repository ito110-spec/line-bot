import google.generativeai as genai
from janome.tokenizer import Tokenizer
import os

# Gemini APIキー（環境変数から取得）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# モデル指定（Gemini 1.5 Flash推奨：速くて安い）
GEMINI_MODEL = "gemini-1.5-flash"

def query_gemini(prompt):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else None
    except Exception as e:
        print(f"Gemini API エラー: {e}")
        return None

def extract_keywords(text):
    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(text)
    keywords = []
    for token in tokens:
        part = token.part_of_speech.split(',')[0]
        if part in ["名詞", "形容詞"]:
            keywords.append(token.base_form)
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

        prompt = (
            f"以下のアニメタイトルについて、それぞれのストーリーの特徴を4つのカテゴリで2つずつ挙げてください。\n"
            f"カテゴリ: 感情要素, ストーリー展開要素, 登場キャラ内面/心理要素, 世界観要素\n"
            f"タイトル一覧: {', '.join(titles)}\n"
            "回答はカテゴリごとに箇条書きで簡潔に。"
        )

        result = query_gemini(prompt)
        if not result:
            return "おすすめを取得中にエラーが発生しました。もう一度やり直してください。"

        keywords = extract_keywords(result)

        anime_search_states[user_id] = {"titles": []}

        return f"おすすめ生成結果:\n{result}\n\n抽出タグ:\n{', '.join(keywords)}\n"

    else:
        titles = state.get("titles", [])
        titles.append(user_msg)
        state["titles"] = titles
        return f"タイトル「{user_msg}」を登録しました。ほかのタイトルか「検索」と入力してください。"
