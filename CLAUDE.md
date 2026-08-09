# morning-news-notify プロジェクト概要
夫婦専用の毎朝ニュース自動通知システム。
毎日 JST 4:30（GitHub Actions cron: UTC 19:30）に自動実行され、
8ヶ国（台湾・中国本土・アメリカ・イギリス・タイ・オーストラリア・日本・ハワイ）の
ニュースを取得し、Claude APIで日本語要約した上で、LINE通知とWebページ公開の
両方で配信する。

## 技術構成

- 言語: Python 3.12（.venv による仮想環境管理）
- ニュース取得: NewsAPI.org（無料プラン、1日100リクエストまで）
- 要約: Anthropic Claude API（claude-sonnet-4-6）
- 通知: LINE Messaging API（個人用LINE公式アカウント、ブロードキャスト配信）
- Webページ: GitHub Pages（mainブランチの /docs フォルダを公開）
- 自動実行: GitHub Actions（.github/workflows/morning-news.yml）

## ファイル構成

- main.py: 全処理のメインスクリプト（このファイル1本で完結させる方針）
- requirements.txt: 依存ライブラリ一覧
- docs/index.html: 自動生成されるWebページ（手動編集しない、main.py実行のたびに上書きされる）
- .env: ローカル用のAPIキー（Gitには絶対にコミットしない、.gitignoreで除外済み）

## 絶対に守るべきルール

- APIキー・トークンの類は、コード内に直接書かない。必ず環境変数（os.getenv）経由で読み込む。
- .env ファイルは絶対にコミットしない。.gitignoreの設定を変更・削除しない。
- GitHub Actionsでの実行時は、GitHub Secretsに登録された値を使う
  （NEWSAPI_KEY / ANTHROPIC_API_KEY / LINE_CHANNEL_ACCESS_TOKEN）。
- LINE通知は「ブロードキャスト配信」または「Flexメッセージ（カルーセル）」で、
  1回の実行につき1〜数通に収める。国ごとにバラバラの独立メッセージとして
  大量送信しない（LINE公式アカウント無料枠：月200通の制限があるため）。
- main.py の関数定義は、必ず呼び出しよりも前（ファイル上部）に配置する。
  if __name__ == "__main__": ブロックは常にファイルの最後に1つだけ。

## コーディング規約

- コミットメッセージは日本語で、変更内容が分かる一文にする
  （例: 「ニュース取得機能を実装」「LINE通知とWebページ生成機能を実装」）。
- 関数には日本語のdocstring（説明コメント）を必ず付ける。
- 新しい国・地域を追加する場合は、COUNTRIES リストに1行追加するだけで
  拡張できる設計を維持する（個別のif分岐を増やさない）。

## 既知の制約・注意点

- NewsAPIの無料プランでは、国によって top-headlines (country=xx) が
  0件になることがある（日本・台湾・中国本土・イギリス・タイ・
  オーストラリアで確認済み）。その場合は everything エンドポイント + 
  ドメイン指定 or キーワード検索に切り替える。
- ハワイは国コードが存在しないため、キーワード検索（q=Hawaii）で対応している。
- GitHub Actionsのワークフローファイルは、必ず .github/workflows/ 
  フォルダの直下に置くこと（.github直下に置くと認識されない）。
- ワークフローファイルの新規作成・変更をpushするには、GitHubトークンに
  workflowスコープが必要（通常のrepoスコープだけでは拒否される）。