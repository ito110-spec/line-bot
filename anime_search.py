import google.generativeai as genai
import os
import time
import traceback
import sys
import subprocess
from fugashi import Tagger

paths = subprocess.getoutput("find / -name mecabrc 2>/dev/null")
print("[DEBUG] mecabrc files found:\n" + paths)


# Gemini APIキー（環境変数から取得）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# モデル指定（Gemini 1.5 Flash推奨：速くて安い）
GEMINI_MODEL = "gemini-1.5-flash"

def query_gemini(prompt, attempts=4):
    if not GEMINI_API_KEY:
        print("[DEBUG] GEMINI_API_KEY が見つかりません。環境変数を確認してください。")
        return None

    for attempt in range(1, attempts + 1):
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(prompt)

            text = None
            if hasattr(response, "text") and response.text:
                text = response.text
            elif isinstance(response, dict) and "candidates" in response:
                text = response["candidates"][0].get("content", "")
            else:
                text = str(response)

            if text:
                print(f"[DEBUG] Gemini 応答内容(attempt {attempt}): {text}")
                return text.strip()
            else:
                print(f"[DEBUG] Gemini 応答が空でした。attempt={attempt}, response={response}")

        except Exception as e:
            print(f"[ERROR] Gemini API エラー (attempt {attempt}): {e}")
            traceback.print_exc()

        if attempt < attempts:
            wait = (2 ** (attempt - 1)) * 5
            print(f"[DEBUG] 再試行まで待機: {wait}s")
            time.sleep(wait)

    print("[DEBUG] Gemini への問い合わせが全て失敗しました。")
    return None

def find_file(name):
    result = subprocess.getoutput(f"find / -name {name} 2>/dev/null")
    files = [line for line in result.split("\n") if os.path.isfile(line)]
    return files[0] if files else None

def find_dic_dir(name):
    """
    mecab-ipadicなどの辞書フォルダの親ディレクトリを返す
    例: /usr/lib/x86_64-linux-gnu/mecab/dic/ipadic なら
         /usr/lib/x86_64-linux-gnu/mecab/dic を返す
    """
    result = subprocess.getoutput(f"find / -type d -name {name} 2>/dev/null")
    dirs = [line for line in result.split("\n") if os.path.isdir(line)]
    if not dirs:
        return None
    dic_path = dirs[0]
    parent_dir = os.path.dirname(dic_path)
    return parent_dir

# mecabrc と辞書の場所を探す
mecabrc_path = find_file("mecabrc")
dic_parent_dir = find_dic_dir("mecab-ipadic")

print(f"[DEBUG] mecabrc: {mecabrc_path}", file=sys.stderr)
print(f"[DEBUG] mecab-ipadic親ディレクトリ: {dic_parent_dir}", file=sys.stderr)

# Tagger 初期化
tagger = None
try:
    args = []
    if mecabrc_path:
        args.append(f"-r {mecabrc_path}")
    if dic_parent_dir:
        args.append(f"-d {dic_parent_dir}")
    tagger = Tagger(" ".join(args))
    print("[DEBUG] fugashi Tagger初期化成功", file=sys.stderr)
except Exception as e:
    print("[ERROR] fugashi Tagger初期化失敗:", e, file=sys.stderr)

def extract_keywords(text):
    print("[DEBUG] extract_keywords called", file=sys.stderr)
    print("[DEBUG] 入力テキスト:", repr(text), file=sys.stderr)

    if not text:
        print("[WARN] 入力テキストが空です", file=sys.stderr)
        return []

    if tagger is None:
        print("[ERROR] Taggerが初期化されていません", file=sys.stderr)
        return []

    keywords = []
    for word in tagger(text):
        print(f"[DEBUG] surface={word.surface}, feature={word.feature}", file=sys.stderr)
        pos = word.feature.split(",")[0]
        if pos in ("名詞", "形容詞"):
            keywords.append(word.surface)

    keywords = sorted(set(keywords))
    print("[DEBUG] 抽出キーワード:", keywords, file=sys.stderr)
    return keywords


def handle_anime_search(user_id, user_msg, anime_search_states):
    print(f"[DEBUG] user_id={user_id}, user_msg={user_msg}")

    user_msg = user_msg.strip().lower()
    state = anime_search_states.get(user_id)
    if state is None:
        anime_search_states[user_id] = {"titles": []}
        state = anime_search_states[user_id]

    if user_msg == "検索":
        titles = state.get("titles", [])
        if not titles:
            return "まだアニメタイトルが入力されていません。好きなアニメを教えてください。"

        prompt = (
            f"以下のアニメタイトルについて、それぞれのストーリーの特徴を4つのカテゴリで3つずつ挙げてください。\n"
            f"カテゴリ: 感情要素, ストーリー展開要素, 登場キャラ内面/心理要素, 世界観要素\n"
            f"タイトル一覧: {', '.join(titles)}\n"
            "回答はカテゴリごとに箇条書きで簡潔に。"
        )

        print("[DEBUG] Geminiに問い合わせるプロンプト:", prompt)

        result = query_gemini(prompt)

        print("[DEBUG] Geminiからの応答:", result)

        if not result:
            return "おすすめを取得中にエラーが発生しました。もう一度やり直してください。"

        keywords = extract_keywords(result)

        # 検索完了後に状態リセット
        anime_search_states[user_id] = {"titles": []}

        return f"おすすめ生成結果:\n{result}\n\n抽出タグ:\n{', '.join(keywords)}\n"

    else:
        titles = state.get("titles", [])
        titles.append(user_msg)
        state["titles"] = titles
        return f"タイトル「{user_msg}」を登録しました。ほかのタイトルか「検索」と入力してください。"
