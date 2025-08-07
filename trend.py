from pytrends.request import TrendReq
import re
from collections import defaultdict
import time
import random

def extract_main_and_sub_related(user_input: str, max_results=10):
    try:
        query = user_input.strip()
        time.sleep(random.uniform(6, 10))  # 強制ウェイト

        pytrends.build_payload([query], geo='JP', timeframe='now 1-d')

        # リトライ付きで取得
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
                    raise e

        df = related.get(query, {}).get('rising')
        if df is None or df.empty:
            return "関連キーワードが見つかりませんでした。"

        word_scores = defaultdict(int)
        original_rows = []
        used_words = set([query])  # 検索語自体は最初から使用済みに

        # 関連ワードを収集
        for row in df.itertuples():
            full_query = row.query
            score = int(row.value)
            original_rows.append((full_query, score))

            cleaned_full_query = full_query.replace(query, '').strip()
            words = [w for w in re.split(r'\s+', cleaned_full_query) if len(w) > 1]
            for w in words:
                if w not in used_words:
                    word_scores[w] += score

        sorted_main = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        results = []

        for main_word, main_score in sorted_main:
            if main_word in used_words:
                continue  # 使用済みワードはスキップ

            sub_words = []
            sub_candidates = []

            # スコアマーク
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
                    candidates = [w.strip() for w in cleaned.split() if w.strip() and w != query and w != main_word]

                    for w in candidates:
                        if w not in used_words and len(w) > 1 and w not in sub_words:
                            sub_words.append(w)
                            if len(sub_words) >= 3:
                                break

            # 使用済みに登録（メイン＋サブ）
            used_words.add(main_word)
            used_words.update(sub_words)

            sub_str = "、".join(sub_words) if sub_words else "なし"
            results.append(f"{score_icon}{main_word}(+{main_score}%)\n┗ｻﾌﾞ関連:{sub_str}")

            if len(results) >= max_results:
                break

            time.sleep(random.uniform(0.5, 1.2))

        return "\n".join(results)

    except Exception as e:
        import traceback
        return f"エラーが発生しました：\n{traceback.format_exc()}"
