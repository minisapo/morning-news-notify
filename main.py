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

# 国ごとの設定
# country: NewsAPIのtop-headlinesで使う国コード
# domains: 特定ニュースサイトのドメインから拾いたい場合
# query: キーワード検索したい場合（国コードが無い/ヒットしない地域向け）
COUNTRIES = [
    {"name": "台湾", "query": "Taiwan"},
    {"name": "中国本土", "query": "China"},
    {"name": "アメリカ", "country": "us"},
    {"name": "イギリス", "query": "UK OR Britain"},
    {"name": "タイ", "query": "Thailand"},
    {"name": "オーストラリア", "query": "Australia"},
    {"name": "日本", "domains": "nhk.or.jp,asahi.com,mainichi.jp"},
    {"name": "ハワイ", "query": "Hawaii"},
]


def fetch_country_articles(country=None, domains=None, query=None):
    """国ごとの設定に応じて記事を取得"""
    if domains:
        url = "https://newsapi.org/v2/everything"
        params = {
            "apiKey": NEWSAPI_KEY,
            "domains": domains,
            "sortBy": "publishedAt",
            "pageSize": 10,
        }
    elif query:
        url = "https://newsapi.org/v2/everything"
        params = {
            "apiKey": NEWSAPI_KEY,
            "q": query,
            "sortBy": "publishedAt",
            "pageSize": 10,
        }
    else:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": NEWSAPI_KEY,
            "country": country,
            "pageSize": 10,
        }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("articles", [])


def summarize_country(name, articles):
    """1ヶ国分の記事を「政治経済/エンタメ/その他」に分類し、見出し＋詳細で整理"""
    if not articles:
        return f"（{name}の記事が取得できませんでした）"

    titles = "\n".join(f"- {a.get('title', '')}" for a in articles)
    prompt = f"""以下は「{name}」の今日のニュース見出し一覧です。
この中から、以下の3つのジャンルそれぞれについて最も注目すべき記事を1つずつ選び、日本語の見出しと2〜3行の詳細説明を作成してください。

- 政治経済
- エンタメ
- その他（社会・国際・スポーツなど）

該当する記事がジャンル内に見当たらない場合は、そのジャンルを省略してください（無理に当てはめないでください）。

出力形式（このフォーマットを厳守してください。他の文章は一切付け加えないでください）:
■政治経済：（日本語見出し）
（詳細説明）

■エンタメ：（日本語見出し）
（詳細説明）

■その他：（日本語見出し）
（詳細説明）

元の見出し一覧:
{titles}
"""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


def build_flex_carousel(country_summaries):
    """国ごとの要約をLINE Flexメッセージ（カルーセル）用に組み立てる"""
    bubbles = []
    for name, summary in country_summaries:
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": name, "weight": "bold", "size": "lg", "color": "#ffffff"}
                ],
                "backgroundColor": "#3B5998",
                "paddingAll": "12px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": summary, "wrap": True, "size": "sm"}
                ]
            }
        }
        bubbles.append(bubble)

    return {
        "type": "carousel",
        "contents": bubbles
    }


def send_line_flex_broadcast(country_summaries):
    """国別ニュースをFlexメッセージ(カルーセル)として1通で配信"""
    today = datetime.now().strftime("%Y年%m月%d日")
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    data = {
        "messages": [
            {
                "type": "flex",
                "altText": f"朝の世界ニュース - {today}",
                "contents": build_flex_carousel(country_summaries)
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    print("LINE送信完了（Flexカルーセル）")


def generate_html(country_summaries):
    """国別の要約を1ページのWebページとして出力"""
    today = datetime.now().strftime("%Y年%m月%d日")

    sections = ""
    for name, summary in country_summaries:
        summary_html = summary.replace("\n", "<br>")
        sections += f"""
<section>
  <h2>{name}</h2>
  <p>{summary_html}</p>
</section>
"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>朝の世界ニュース - {today}</title>
<style>
  body {{ font-family: sans-serif; max-width: 700px; margin: 40px auto; padding: 0 16px; line-height: 1.8; }}
  h1 {{ font-size: 1.4em; border-bottom: 2px solid #333; padding-bottom: 8px; }}
  section {{ margin-bottom: 24px; }}
  h2 {{ font-size: 1.1em; color: #3B5998; border-left: 4px solid #3B5998; padding-left: 8px; }}
  p {{ white-space: pre-wrap; }}
</style>
</head>
<body>
<h1>朝の世界ニュース - {today}</h1>
{sections}
</body>
</html>"""

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Webページ生成完了: docs/index.html")


if __name__ == "__main__":
    country_summaries = []
    for c in COUNTRIES:
        articles = fetch_country_articles(
            country=c.get("country"),
            domains=c.get("domains"),
            query=c.get("query"),
        )
        summary = summarize_country(c["name"], articles)
        print(f"=== {c['name']} ===")
        print(summary)
        print()
        country_summaries.append((c["name"], summary))

    generate_html(country_summaries)
    send_line_flex_broadcast(country_summaries)