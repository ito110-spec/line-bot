from pytrends.request import TrendReq
import re
from collections import defaultdict
import time
import random

pytrends = TrendReq(hl='ja-JP', tz=540)

def extract_main_and_sub_related(user_input: str, max_results=10):
    return "🔴東京(+1234%)\n┗ｻﾌﾞ関連: 旅行、観光、グルメ\n🟠渋谷(+234%)|\n┗ｻﾌﾞ関連: 原宿、109、カフェ"

# def extract_main_and_sub_related(user_input: str, max_results=10):
#     try:
#         query = user_input.strip()
#         pytrends.build_payload([query], geo='JP', timeframe='now 1-d')
#         related = pytrends.related_queries()
#         df = related.get(query, {}).get('rising')

#         print("related_queries result:", related)

#         if df is None or df.empty:
#             return "関連キーワードが見つかりませんでした。"

#         word_scores = defaultdict(int)
#         original_rows = []

#         for row in df.itertuples():
#             full_query = row.query
#             score = int(row.value)  # 修正：valueは数値なのでそのままint化

#             original_rows.append((full_query, score))

#             # 検索語を一括で除去してから分解
#             cleaned_full_query = full_query.replace(query, '').strip()
#             words = [w for w in re.split(r'\s+', cleaned_full_query) if len(w) > 1]
#             for w in words:
#                 word_scores[w] += score

#         # メイン関連ワードをスコア順に並べる
#         sorted_main = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
#         results = []

#         for main_word, main_score in sorted_main[:max_results]:
#             sub_words = []

#             for main_word, main_score in sorted_main[:max_results]:
#                 sub_words = []
            
#                 # 🔊🔉🔈のスコアマークをつける
#                 if main_score >= 1000:
#                     score_icon = "🔴"
#                 elif main_score >= 100:
#                     score_icon = "🟠"
#                 elif main_score >= 10:
#                     score_icon = "🟡"
#                 else:
#                     score_icon = ""
            
#                 for full_query, score in original_rows:
#                     if main_word in full_query and query in full_query:
#                         cleaned = re.sub(query, '', full_query)
#                         cleaned = re.sub(main_word, '', cleaned)
#                         sub_parts = [w.strip() for w in cleaned.split() if w.strip() and w != main_word and w != query]
            
#                         for w in sub_parts:
#                             if w not in sub_words and len(w) > 1:
#                                 sub_words.append(w)
#                                 if len(sub_words) >= 3:
#                                     break
            
#                 sub_str = "、".join(sub_words) if sub_words else "なし"
#                 results.append(f"{score_icon}{main_word}({main_score})\n┗ｻﾌﾞ関連:{sub_str}")
#                 time.sleep(random.uniform(1, 3))  # レート制限対策


#         return "\n".join(results)

#     except Exception as e:
#         import traceback
#         return f"エラーが発生しました：\n{traceback.format_exc()}"
