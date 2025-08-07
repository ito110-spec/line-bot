from pytrends.request import TrendReq
import re
from collections import defaultdict
import time
import random
import urllib.parse

pytrends = TrendReq(hl='ja-JP', tz=540)

def make_news_link(base_query: str, main_word: str, sub_word: str):
    q = f"{base_query} {main_word} {sub_word}"
    q_encoded = urllib.parse.quote(q)
    return f"https://news.google.com/search?q={q_encoded}&hl=ja&gl=JP&ceid=JP:ja"

def extract_main_and_sub_related(user_input: str, max_results=10):
    try:
        query = user_input.strip()

        # ★ Googleリクエスト前に強制ウェイト（6～10秒ランダム）
        time.sleep(random.uniform(6, 10))

        # ★ build_payload（これは基本的にOK）
        pytrends.build_payload([query], geo='JP', timeframe='now 1-d')

        # ★ related_queries にリトライ付きでアクセス
        for attempt in range(3):
            try:
                related = pytrends.related_queries()
                break
            except Exception as e:
                if attempt < 2:
                    wait = 15 + attempt * 10
                    print(f"429 or other error, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise e  # 最終的に失敗

        df = related.get(query, {}).get('rising')

        if df is None or df.empty:
            return "関連キーワードが見つかりませんでした。"

        word_scores = defaultdict(int)
        original_rows = []

        for row in df.itertuples():
            full_query = row.query
            score = int(row.value)
            original_rows.append((full_query, score))

            cleaned_full_query = full_query.replace(query, '').strip()
            words = [w for w in re.split(r'\s+', cleaned_full_query) if len(w) > 1]
            for w in words:
                word_scores[w] += score

        sorted_main = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        results = []

        for main_word, main_score in sorted_main[:max_results]:
            sub_links = []

            # 🔴🟠🟡：スコアに応じたアイコン
            if main_score >= 1000:
                score_icon = "🔴"
            elif main_score >= 100:
                score_icon = "🟠"
            elif main_score >= 10:
                score_icon = "🟡"
            else:
                score_icon = ""

            for full_query, score in original_rows:
                if main_word in full_query and query in full_query:
                    cleaned = re.sub(query, '', full_query)
                    cleaned = re.sub(main_word, '', cleaned)
                    sub_parts = [w.strip() for w in cleaned.split() if w.strip() and w != main_word and w != query]

                    for w in sub_parts:
                        if w not in sub_links and len(w) > 1:
                            link = make_news_link(query, main_word, w)
                            sub_links.append(f"[{w}]({link})")
                            if len(sub_links) >= 3:
                                break

            sub_str = "、".join(sub_links) if sub_links else "なし"
            results.append(f"{score_icon}{main_word}(+{main_score}%)\n┗ｻﾌﾞ関連:{sub_str}")

            # 結果生成側にも軽めのウェイト
            time.sleep(random.uniform(0.5, 1.2))

        return "\n".join(results)

    except Exception as e:
        import traceback
        return f"エラーが発生しました：\n{traceback.format_exc()}"
