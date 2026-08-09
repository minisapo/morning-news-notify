import os
import requests
from dotenv import load_dotenv

# .env ファイルを読み込む
load_dotenv()

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


if __name__ == "__main__":
    print("=== 政治・一般 ===")
    for a in fetch_top_headlines(category="general"):
        print("-", a["title"])

    print("\n=== 経済 ===")
    for a in fetch_top_headlines(category="business"):
        print("-", a["title"])

    print("\n=== エンタメ ===")
    for a in fetch_top_headlines(category="entertainment"):
        print("-", a["title"])

    print("\n=== ローカル（日本） ===")
    for a in fetch_japan_news():
        print("-", a["title"])

    print("\n=== トリップ ===")
    for a in fetch_everything("travel"):
        print("-", a["title"])