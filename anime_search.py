import google.generativeai as genai
from janome.tokenizer import Tokenizer
import os
import time, traceback

# Gemini APIキー（環境変数から取得）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# モデル指定（Gemini 1.5 Flash推奨：速くて安い）
GEMINI_MODEL = "gemini-1.5-flash"

def query_gemini(prompt, attempts=4):
    """Gemini に問い合わせ。失敗時は指数バックオフでリトライ。
       ログを詳細に出すので原因特定に使ってください。"""
    if not os.getenv("GEMINI_API_KEY"):
        print("[DEBUG] GEMINI_API_KEY が見つかりません。環境変数を確認してください。")
        return None

    for attempt in range(1, attempts + 1):
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            # 必要なら max_output_tokens 等パラメータを加える
            response = model.generate_content(prompt)
            text = None
            # response の形が変わるライブラリ差に備える
            if hasattr(response, "text") and response.text:
                text = response.text
            elif isinstance(response, dict) and "candidates" in response:
                # まれに dict 返り値のケースに備え
                text = response["candidates"][0].get("content", "")
            else:
                text = str(response)

            if text:
                return text.strip()
            else:
                print(f"[DEBUG] Gemini 応答が空でした。attempt={attempt}, response={response}")
                # 続けてリトライ

        except Exception as e:
            print(f"[ERROR] Gemini API エラー (attempt {attempt}): {e}")
            traceback.print_exc()

        # リトライ待ち（指数バックオフ）
        if attempt < attempts:
            wait = (2 ** (attempt - 1)) * 5  # 5s,10s,20s...
            print(f"[DEBUG] 再試行まで待機: {wait}s")
            time.sleep(wait)

    # 全滅
    print("[DEBUG] Gemini への問い合わせが全て失敗しました。")
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

        print("[DEBUG] Geminiに問い合わせるプロンプト:", prompt)   # ← ここ追加

        result = query_gemini(prompt)

        print("[DEBUG] Geminiからの応答:", result)   # ← ここ追加

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
