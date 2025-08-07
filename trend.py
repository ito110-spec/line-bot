import time
import random
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import traceback

# pytrends クライアント初期化（日本、東京）
pytrends = TrendReq(hl='ja-JP', tz=540)

user_access_log = {}
cooldown_users = {}

def parse_query(user_input: str):
    return [t.strip() for t in user_input.split("、") if t.strip()]

def can_use_trend(user_id):
    now = datetime.now()
    if user_id in cooldown_users:
        if now < cooldown_users[user_id]:
            remaining = cooldown_users[user_id] - now
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            return False, f"使いすぎです！あと{minutes}分{seconds}秒ほどお待ちください。"
        else:
            del cooldown_users[user_id]

    logs = user_access_log.get(user_id, [])
    logs = [t for t in logs if now - t < timedelta(minutes=5)]

    if len(logs) >= 4:
        cooldown_users[user_id] = now + timedelta(minutes=15)
        return False, "4回使いました！15分間クールタイムです。"

    logs.append(now)
    user_access_log[user_id] = logs
    return True, None

def get_related_keywords(user_input: str) -> str:
    try:
        query_terms = parse_query(user_input)
        if not query_terms:
            return "キーワードが空です。"

        pytrends.build_payload(query_terms, timeframe="now 4-H", geo="JP")
        related = pytrends.related_queries()

        combined = {}
        for q in query_terms:
            top_df = related.get(q, {}).get("top")
            if top_df is not None and not top_df.empty:
                for row in top_df.itertuples():
                    word = row.query
                    # 検索語を全部除去して残りをcleaned_wordに
                    cleaned_word = word
                    for term in query_terms:
                        cleaned_word = cleaned_word.replace(term, "")
                    cleaned_word = cleaned_word.strip()

                    # 1文字以下の語は除外
                    if cleaned_word and len(cleaned_word) > 1:
                        # すでにある語があればスコアの高い方を残す
                        if cleaned_word in combined:
                            combined[cleaned_word] = max(combined[cleaned_word], row.value)
                        else:
                            combined[cleaned_word] = row.value

        if not combined:
            return "関連ワードが見つかりませんでした。"

        sorted_main = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        results = []

        for idx, (main_word, main_score) in enumerate(sorted_main):
            try:
                # メイン関連＋検索語でrising取得（AND検索）
                pytrends.build_payload([main_word] + query_terms, timeframe="now 4-H", geo="JP")
                sub_related = pytrends.related_queries()
                rising_df = sub_related.get(main_word, {}).get("rising")
        
                sub_words = []
                if rising_df is not None and not rising_df.empty:
                    for sub_row in rising_df.itertuples():
                        if (
                            sub_row.query != main_word and
                            not any(q in sub_row.query for q in query_terms)
                        ):
                            sub_words.append(sub_row.query)
                            if len(sub_words) >= 3:
                                break
            except Exception:
                sub_words = []


            related_str = ", ".join(sub_words) if sub_words else "なし"
            results.append(f"{main_word}（+{main_score}）｜急上昇:{related_str}")

            time.sleep(random.uniform(2, 5))

            if len(results) >= 10:
                break

        return "\n".join(results)

    except Exception as e:
        return f"エラーが発生しました：{traceback.format_exc()}"

def handle_trend_search(user_id: str, user_input: str) -> str:
    try:
        can_use, reason = can_use_trend(user_id)
        if not can_use:
            return reason

        time.sleep(random.randint(1, 3))  # レート制限対策
        return get_related_keywords(user_input)

    except Exception:
        return f"エラーが発生しました：\n{traceback.format_exc()}"
