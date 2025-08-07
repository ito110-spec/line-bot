from pytrends.request import TrendReq
import pandas as pd
import re
from collections import defaultdict
import time
import random

pytrends = TrendReq(hl='ja-JP', tz=540)

def extract_main_and_sub_related(user_input: str, max_results=10):
    try:
        # 1. 検索語
        query = user_input.strip()
        pytrends.build_payload([query], geo='JP', timeframe='now 4-H')
        related = pytrends.related_queries()
        df = related.get(query, {}).get('rising')

        if df is None or df.empty:
            return "関連キーワードが見つかりませんでした。"

        # 2. 前処理：スコア・単語分解
        word_scores = defaultdict(int)
        original_rows = []

        for row in df.itertuples():
            full_query = row.query
            percent_match = re.search(r'(\d+(,\d+)?)(?=%)', row.value)
            score = int(percent_match.group(1).replace(',', '')) if percent_match else row.value
            original_rows.append((full_query, score))

            # 検索語を除外して残りの語を分解
            words = [w for w in re.split(r'\s+', full_query) if w != query]
            for w in words:
                if len(w) > 1:
                    word_scores[w] += score

        # 3. メイン関連ワードをスコア順に
        sorted_main = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        results = []

        for main_word, main_score in sorted_main[:max_results]:
            sub_words = []

            for full_query, score in original_rows:
                if main_word in full_query and query in full_query:
                    cleaned = re.sub(query, '', full_query)
                    cleaned = re.sub(main_word, '', cleaned)
                    sub_parts = [w.strip() for w in cleaned.split() if w.strip() and w != main_word and w != query]

                    for w in sub_parts:
                        if w not in sub_words and len(w) > 1:
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
