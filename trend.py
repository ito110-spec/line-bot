import time
import random
from datetime import datetime, timedelta
from collections import Counter
from pytrends.request import TrendReq

# pytrends クライアント初期化（日本、東京）
pytrends = TrendReq(hl='ja-JP', tz=540)

# 利用ログ記録
user_access_log = {}  # {user_id: [datetime1, datetime2, ...]}
cooldown_users = {}   # {user_id: cooldown_end_datetime}


def parse_query(user_input: str):
    """
    「、」区切りで複数語AND検索に変換
    """
    return [t.strip() for t in user_input.split("、") if t.strip()]


def can_use_trend(user_id):
    """
    利用回数チェック & クールダウン判定
    """
    now = datetime.now()

    # クールタイム中？
    if user_id in cooldown_users:
        if now < cooldown_users[user_id]:
            remaining = cooldown_users[user_id] - now
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            return False, f"使いすぎです！あと{minutes}分{seconds}秒ほどお待ちください。"
        else:
            del cooldown_users[user_id]

    # 過去5分のリクエスト履歴を確認
    logs = user_access_log.get(user_id, [])
    logs = [t for t in logs if now - t < timedelta(minutes=5)]

    if len(logs) >= 4:
        cooldown_users[user_id] = now + timedelta(minutes=15)
        return False, "4回使いました！15分間クールタイムです。"

    # 使用可能 → 時間記録を更新
    logs.append(now)
    user_access_log[user_id] = logs
    return True, None


def get_related_keywords(user_input: str) -> str:
    """
    指定ワードに関連する上昇キーワードを返す（Google Trends）
    """
    try:
        query_terms = parse_query(user_input)
        if not query_terms:
            return "キーワードが空です。"

        # クエリ送信
        pytrends.build_payload(query_terms, timeframe="now 1-H", geo="JP")
        related = pytrends.related_queries()

        rising = related.get(query_terms[0], {}).get("rising")

        if rising is None or rising.empty:
            return "関連ワードが見つかりませんでした。"

        # 検索語句群を除外対象のセットを作る（単語単体のみ）
        exclude_words = set(query_terms)

        result_lines = []
        count = 0
        for row in rising.itertuples():
            # 除外語に含まれていなければ表示
            if row.query not in exclude_words:
                count += 1

                # 感情判定（valueが正なら＋、負なら－）
                emotion = "＋" if row.value > 0 else "－"

                # その関連ワードを再度検索して、上位3関連ワードを取得
                pytrends.build_payload([row.query], timeframe="now 1-H", geo="JP")
                sub_related = pytrends.related_queries()
                sub_rising = sub_related.get(row.query, {}).get("rising")

                related_words = []
                if sub_rising is not None and not sub_rising.empty:
                    for sub_row in sub_rising.itertuples():
                        if sub_row.query not in exclude_words and sub_row.query != row.query:
                            related_words.append(sub_row.query)
                            if len(related_words) >= 3:
                                break

                related_str = ", ".join(related_words) if related_words else "なし"

                # 1行にまとめて追加
                line = f"{row.query}（+{row.value}）｜感情：{emotion}｜関連：{related_str}"
                result_lines.append(line)

                if count >= 20:
                    break

        if count == 0:
            return "関連ワードが見つかりませんでした。"

        header = f"『{'、'.join(query_terms)}』の関連ワードTOP20（過去1時間で上昇中）：\n\n"
        return header + "\n".join(result_lines)

    except Exception as e:
        return f"エラーが発生しました：{e}"


def handle_trend_search(user_id: str, user_input: str) -> str:
    """
    LINE BOT から呼び出す統合関数
    - クールタイムチェック
    - ランダムスリープ
    - トレンド取得
    """
    can_use, reason = can_use_trend(user_id)
    if not can_use:
        return reason

    time.sleep(random.randint(30, 40))  # レート制限対策
    return get_related_keywords(user_input)
