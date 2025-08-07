import time
import random
from datetime import datetime, timedelta
from pytrends.request import TrendReq

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

        pytrends.build_payload(query_terms, timeframe="now 6-H", geo="JP")
        related = pytrends.related_queries()

        top_df = related.get(query_terms[0], {}).get("top")
        rising_df = related.get(query_terms[0], {}).get("rising")

        if top_df is None and rising_df is None:
            return "関連ワードが見つかりませんでした。"

        combined = {}

        if top_df is not None and not top_df.empty:
            for row in top_df.itertuples():
                combined[row.query] = row.value

        if rising_df is not None and not rising_df.empty:
            for row in rising_df.itertuples():
                # すでにある場合は value を加算（または平均なども可）
                if row.query in combined:
                    combined[row.query] += row.value
                else:
                    combined[row.query] = row.value

        exclude_words = set(query_terms)
        results = []

        # 降順でスコア順に並べる
        sorted_items = sorted(combined.items(), key=lambda x: x[1], reverse=True)

        for idx, (word, score) in enumerate(sorted_items):
            if word in exclude_words:
                continue

            emotion = "＋" if score > 0 else "－"

            # サブ関連ワード取得（TOP）
            pytrends.build_payload([word], timeframe="now 6-H", geo="JP")
            sub_related = pytrends.related_queries()
            sub_top = sub_related.get(word, {}).get("top")

            sub_words = []
            if sub_top is not None and not sub_top.empty:
                for sub_row in sub_top.itertuples():
                    if sub_row.query != word and sub_row.query not in exclude_words:
                        sub_words.append(sub_row.query)
                        if len(sub_words) >= 3:
                            break

            related_str = ", ".join(sub_words) if sub_words else "なし"
            results.append(f"{word}（+{score}）｜感情：{emotion}｜関連：{related_str}")

            # ランダムスリープ（2〜5秒）
            time.sleep(random.uniform(2, 5))

            if len(results) >= 10:
                break

        if not results:
            return "関連ワードが見つかりませんでした。"

        header = f"『{'、'.join(query_terms)}』の関連ワードTOP10（過去6時間）：\n\n"
        return header + "\n".join(results)

    except Exception as e:
        return f"エラーが発生しました：{e}"


def handle_trend_search(user_id: str, user_input: str) -> str:
    can_use, reason = can_use_trend(user_id)
    if not can_use:
        return reason

    time.sleep(random.randint(1, 3))  # 軽めのクールダウン
    return get_related_keywords(user_input)
