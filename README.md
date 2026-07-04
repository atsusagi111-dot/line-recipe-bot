# 🍳 LINEレシピ提案ボット

食材（と、あれば調味料）をLINEで送るだけで、
- 大人2人分の「ご飯がすすむ」絶品レシピ
- 1歳児向けの離乳食レシピ

をAIが考えて、完成イメージ画像つきで返してくれるプログラミング初心者向けのシステムです。

---

## 1. これは何をするプログラムなの？

1. ユーザーがLINEの公式アカウントに「食材：豚肉、キャベツ／調味料：醤油、みりん」のようなメッセージを送る
2. サーバー（このプログラム）がメッセージを受け取り、OpenAIのAI（GPT-4o）に「この食材だけを使ったレシピを考えて」と依頼する
3. AIが考えたレシピの内容から、DALL-E 3というAIで完成イメージ画像を生成する
4. レシピ名・材料・作り方・ポイント・栄養バランスの説明・画像を、LINEの見やすいカード形式（Flex Message）でユーザーに送り返す

1人が1日に提案してもらえる回数は3回までに制限されています（AIの利用には料金がかかるため）。

## 2. ファイルの役割（何がどこに書いてあるか）

| ファイル | 役割 |
|---|---|
| `app.py` | プログラムの入口。LINEからのメッセージを受け取り、他のファイルの機能をつなぎ合わせる |
| `config.py` | `.env`に書いた設定値（APIキーなど）を読み込む係 |
| `message_parser.py` | LINEのメッセージ文章を「食材リスト」「調味料リスト」に分解する係 |
| `openai_client.py` | OpenAIのAIにレシピ文章と画像を作ってもらう係 |
| `flex_builder.py` | レシピの内容を、LINEのリッチなカード表示（Flex Message）に組み立てる係 |
| `usage_limiter.py` | 「1人1日3回まで」という利用制限を管理する係 |
| `requirements.txt` | このプログラムを動かすために必要なライブラリの一覧 |
| `Procfile` / `render.yaml` / `runtime.txt` | Render（サーバーを借りるサービス）にデプロイするための設定ファイル |
| `.env` | APIキーなどの秘密情報を書くファイル（絶対に公開しないこと） |

## 3. 事前に用意するもの

- LINE Developersのアカウント（LINE公式アカウントのMessaging API設定）
- OpenAIのアカウントとAPIキー（GPT-4oとDALL-E 3を使うため、課金設定が必要です）
- Renderのアカウント（サーバーを無料〜低価格で借りられるサービス）

## 4. ローカルで動かす準備（自分のパソコンで試す）

### 4-1. 必要なライブラリをインストール

すでに`.venv`という仮想環境を作成し、必要なライブラリはインストール済みです。
もし新しい環境で1からやり直す場合は、次のコマンドで再インストールできます。

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 4-2. `.env`ファイルに自分のキーを設定する

`.env.example`をコピーして`.env`という名前で保存し、以下の項目を自分の値に書き換えてください。

```
LINE_CHANNEL_SECRET=（LINE Developersコンソールの「チャネル基本設定」タブで確認）
LINE_CHANNEL_ACCESS_TOKEN=（LINE Developersコンソールの「Messaging API設定」タブで発行）
OPENAI_API_KEY=（https://platform.openai.com/api-keys で発行）
```

`.env`ファイルはAPIキーという「パスワードのようなもの」が入っているため、**GitHubなどに絶対に公開しないでください**（`.gitignore`ですでに除外設定はしてあります）。

### 4-3. ローカルで起動して動作確認する

```powershell
.venv\Scripts\python app.py
```

`http://127.0.0.1:5000/` にブラウザでアクセスして「LINE recipe bot is running.」と表示されればOKです。
ただし、LINEから実際にメッセージを送ってテストするには、インターネット上に公開されたURLが必要なので、次のRenderへのデプロイが必要です。

## 5. Renderへのデプロイ手順（インターネットに公開する）

1. このフォルダの中身をGitHubリポジトリにアップロードする
2. [Render](https://render.com/) にログインし、「New +」→「Web Service」を選択
3. アップロードしたGitHubリポジトリを選択する
4. 以下を設定する
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. 「Environment」の設定画面で、`.env`に書いたのと同じ内容を1つずつ環境変数として登録する
   - `LINE_CHANNEL_SECRET`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `OPENAI_API_KEY`
6. デプロイが完了すると、`https://（サービス名）.onrender.com` のようなURLが発行される

## 6. LINE Developersでの設定（webhookのつなぎこみ）

1. LINE Developersコンソールの「Messaging API設定」タブを開く
2. 「Webhook URL」に、Renderで発行されたURル + `/callback` を入力する
   - 例: `https://line-recipe-bot.onrender.com/callback`
3. 「Webhookの利用」をオンにする
4. 「応答メッセージ」はオフにしておく（LINEの自動応答と競合しないように）

これで、LINEの公式アカウントにメッセージを送ると、このプログラムが応答するようになります。

## 7. 実際の使い方（LINEでの送り方）

```
食材：豚肉、キャベツ、人参
調味料：醤油、みりん
```

- 「調味料：」の行はなくてもOKです
- 食材は、読点（、）・カンマ・スペースなどで区切って複数入力できます
- 1日に提案してもらえる回数は3回までです（`config.py`の`DAILY_LIMIT`で変更可能）

## 8. 注意点・費用について

- GPT-4oでの文章生成、DALL-E 3での画像生成のどちらも**OpenAIの従量課金**が発生します。使いすぎに注意してください。
- 画像生成には数十秒かかるため、LINEには先に「考え中です」という即時返信を送り、できあがったらプッシュ通知で送る、という2段階の仕組みになっています。
- 離乳食レシピは、はちみつを使わない・薄味にする・細かく刻む/柔らかく煮るなど、1歳児向けに安全性を配慮するようAIに指示しています。ただし実際に与える前は、必ず大人が内容を確認してください。
