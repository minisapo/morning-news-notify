import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

# .env ファイルを読み込む
load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

client = Anthropic(api_key=ANTHROPIC_API_KEY)


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
        params["country"] = "us"

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


def send_line_broadcast(text):
    """LINE公式アカウントの友だち全員にテキストメッセージを一斉配信"""
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    data = {
        "messages": [
            {"type": "text", "text": text}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    print("LINE送信完了")


def generate_html(summary_text):
    """要約結果を簡易HTMLページとしてdocsフォルダに出力"""
    today = datetime.now().strftime("%Y年%m月%d日")
    html_body = summary_text.replace("\n", "<br>")

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>朝の世界ニュース - {today}</title>
<style>
  body {{ font-family: sans-serif; max-width: 700px; margin: 40px auto; padding: 0 16px; line-height: 1.8; }}
  h1 {{ font-size: 1.4em; border-bottom: 2px solid #333; padding-bottom: 8px; }}
</style>
</head>
<body>
<h1>朝の世界ニュース - {today}</h1>
<div>{html_body}</div>
</body>
</html>"""

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Webページ生成完了: docs/index.html")


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

    generate_html(summary)
    send_line_broadcast(summary)