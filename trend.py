import snscrape.modules.twitter as sntwitter
import datetime
from janome.tokenizer import Tokenizer
from collections import Counter

def search_tweets(query, limit=300):
    now = datetime.datetime.utcnow()
    since = (now - datetime.timedelta(hours=1)).isoformat(timespec="seconds") + "Z"
    tweets = []
    for tweet in sntwitter.TwitterSearchScraper(f"{query} since_time:{since}").get_items():
        tweets.append(tweet.content)
        if len(tweets) >= limit:
            break
    return tweets

def parse_query(user_input):
    terms = [t.strip() for t in user_input.split("、")]
    return " ".join(f'"{term}"' for term in terms)

def extract_keywords(texts):
    tokenizer = Tokenizer()
    words = []
    for text in texts:
        for token in tokenizer.tokenize(text):
            if token.part_of_speech.startswith("名詞"):
                word = token.surface
                if len(word) > 1:  # 1文字の単語は除外
                    words.append(word)
    return Counter(words).most_common(10)

def get_related_words(user_input):
    query = parse_query(user_input)
    tweets = search_tweets(query)
    if not tweets:
        return "ツイートが見つかりませんでした。"

    ranking = extract_keywords(tweets)
    result = f"『{user_input}』の関連ワードTOP10：\n\n"
    for i, (word, count) in enumerate(ranking, 1):
        result += f"{i}. {word}（{count}件）\n"
    return result
