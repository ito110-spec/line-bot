from groq import Groq
from janome.tokenizer import Tokenizer
import os

# Groq API キーを環境変数から取得
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq クライアント初期化
client = Groq(api_key=GROQ_API_KEY)

# モデル指定（例：llama3-8b-8192）
GROQ_MODEL = "mixtral-8x7b-32768"

def query_groq(prompt):
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "あなたはアニメのストーリー要素に詳しいAIです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API エラー: {e}")
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

        result = query_groq(prompt)
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
