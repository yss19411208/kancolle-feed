# Python 3.11以上 / Scweet 5.3
# GitHub Actions上で実行される。.envは使わず環境変数から直接読む

import os
import sys
import json
from datetime import datetime, timezone, timedelta

X_AUTH_TOKEN = os.environ.get("X_AUTH_TOKEN", "")
TARGET_USERNAME = "KanColle_STAFF"
TWEET_LIMIT     = 5
OUTPUT_PATH     = "docs/latest.json"
JST             = timezone(timedelta(hours=9))

if not X_AUTH_TOKEN:
    print("エラー: 環境変数 X_AUTH_TOKEN が未設定です")
    sys.exit(1)

try:
    from Scweet import Scweet
except ImportError as error:
    print(f"エラー: Scweetのimportに失敗しました: {error}")
    sys.exit(1)

print(f"@{TARGET_USERNAME} のツイートを取得中...")

try:
    scweet = Scweet(auth_token=X_AUTH_TOKEN)
    tweets = scweet.get_profile_tweets([TARGET_USERNAME], limit=TWEET_LIMIT)
except Exception as error:
    print(f"エラー: 取得に失敗しました: {error}")
    sys.exit(1)

if not tweets or len(tweets) == 0:
    print("ツイートが取得できませんでした。既存のJSONを上書きしません。")
    sys.exit(0)

# 既存のJSONを読み込んで最新ツイートのURLと比較
existing_latest_url = None
if os.path.exists(OUTPUT_PATH):
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as existing_file:
            existing_data = json.load(existing_file)
            if existing_data.get("tweets"):
                existing_latest_url = existing_data["tweets"][0].get("url", "")
    except Exception:
        pass  # 読み込み失敗時は比較せずそのまま上書き

# 新しいツイートのURLを取得
new_latest_url = (
    tweets[0].get("TweetURL")
    or tweets[0].get("tweet_url")
    or ""
)

# デバッグ用：取得できたツイートのURLを全件表示
print(f"既存JSON最新URL: {existing_latest_url}")
print(f"取得した最新URL: {new_latest_url}")
for i, tweet in enumerate(tweets):
    url = tweet.get("TweetURL") or tweet.get("tweet_url") or ""
    print(f"  tweets[{i}]: {url}")

if new_latest_url and new_latest_url == existing_latest_url:
    print("新しいツイートはありません。スキップします。")
    sys.exit(0)

# JSONに変換して保存
result = {
    "updated_at": datetime.now(JST).isoformat(),
    "account": TARGET_USERNAME,
    "tweets": []
}

for tweet in tweets:
    result["tweets"].append({
        "timestamp": tweet.get("Timestamp") or tweet.get("timestamp") or "",
        "text":      tweet.get("Tweet")     or tweet.get("text")      or "",
        "likes":     tweet.get("Likes")     or tweet.get("likes")     or 0,
        "retweets":  tweet.get("Retweets")  or tweet.get("retweets")  or 0,
        "url":       tweet.get("TweetURL")  or tweet.get("tweet_url") or "",
    })

os.makedirs("docs", exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
    json.dump(result, output_file, ensure_ascii=False, indent=2)

print(f"保存完了: {OUTPUT_PATH}  ({len(result['tweets'])}件)")
