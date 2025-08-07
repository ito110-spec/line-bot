from pytrends.request import TrendReq
import re
from collections import defaultdict
import time
import random

pytrends = TrendReq(hl='ja-JP', tz=540)

def extract_main_and_sub_related(user_input: str, max_results=10):
    try:
        query = user_input.strip()
        pytrends.build_payload([query], geo='JP', timeframe='now 4-H')
        related = pytrends.related_queries()
        df = related.get(query, {}).get('rising')

        if df is None or df.empty:
            return "関連キーワードが見つかりませんでした。"

        word_scores = defaultdict(int)
        original_rows = []

        for row in df.itertuples():
            full_query = row.query
            score = int(row.value)  # 修正：valueは数値なのでそのままint化

            original_rows.append((full_query, score))

            # 検索語を一括で除去してから分解
            cleaned_full_query = full_query.replace(query, '').strip()
            words = [w for w in re.split(r'\s+', cleaned_full_query) if len(w) > 1]
            for w in words:
                word_scores[w] += score

        # メイン関連ワードをスコア順に並べる
        sorted_main = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        results = []

        for main_word, main_score in sorted_main[:max_results]:
            sub_words = []

            for full_query, score in original_rows:
                if main_word in full_query and query in full_query:
                    # 検索語とメイン関連ワードを除去
                    cleaned = full_query.replace(query, '').replace(main_word, '').strip()
                    sub_parts = [w.strip() for w in re.split(r'\s+', cleaned) if w and w != main_word and w != query and len(w) > 1]

                    for w in sub_parts:
                        if w not in sub_words:
                            sub_words.append(w)
                            if len(sub_words) >= 3:
                                break

            sub_str = "、".join(sub_words) if sub_words else "なし"
            results.append(f"{main_word}（+{main_score}%）｜サブ関連:{sub_str}")

            time.sleep(random.uniform(1, 2))  # レート制限対策

        return "\n".join(results)

    except Exception as e:
        import traceback
        return f"エラーが発生しました：\n{traceback.format_exc()}"
