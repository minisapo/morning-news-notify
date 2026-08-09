import os
import requests
from dotenv import load_dotenv
from anthropic import Anthropic
import os
import requests
from dotenv import load_dotenv

# .env ファイルを読み込む
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=ANTHROPIC_API_KEY)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def fetch_top_headlines(category=None, country=None):
    """カテゴリ別・国別のトップニュースを取得"""
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWSAPI_KEY,
        "pageSize": 5,
    }
    if category:
        params["category"] = category
    if country:
        params["country"] = country
    else:
        params["country"] = "us"  # 世界のニュースは国指定必須なので、まずは米国発を基準にする

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("articles", [])


def fetch_everything(query):
    """キーワード検索でニュースを取得（トリップなど）"""
    url = "https://newsapi.org/v2/everything"
    params = {
        "apiKey": NEWSAPI_KEY,
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("articles", [])
def fetch_japan_news():
    """日本の主要ニュースサイトから記事を取得"""
    url = "https://newsapi.org/v2/everything"
    params = {
        "apiKey": NEWSAPI_KEY,
        "domains": "nhk.or.jp,asahi.com,mainichi.jp",
        "sortBy": "publishedAt",
        "pageSize": 5,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("articles", [])

def summarize_news(news_by_genre):
    """ジャンルごとのニュース記事をClaudeで日本語要約する"""
    # プロンプト用にテキストを組み立てる
    source_text = ""
    for genre, articles in news_by_genre.items():
        source_text += f"\n【{genre}】\n"
        for a in articles:
            title = a.get("title", "")
            source_text += f"- {title}\n"

    prompt = f"""以下は今日の世界のニュース見出し一覧です。ジャンルごとに、日本語で3行以内の簡潔な要約を作成してください。
見出しの単純な翻訳ではなく、全体像がわかるようにまとめてください。

{source_text}

出力形式（このフォーマットを厳守してください）:
【政治・一般】
（要約）

【経済】
（要約）

【エンタメ】
（要約）

【ローカル（日本）】
（要約）

【トリップ】
（要約）
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


if __name__ == "__main__":
    news_by_genre = {
        "政治・一般": fetch_top_headlines(category="general"),
        "経済": fetch_top_headlines(category="business"),
        "エンタメ": fetch_top_headlines(category="entertainment"),
        "ローカル（日本）": fetch_japan_news(),
        "トリップ": fetch_everything("travel"),
    }

    summary = summarize_news(news_by_genre)
    print(summary)