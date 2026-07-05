# このファイルは「.envファイルに書いた設定値」をPythonから読み込むための係です。
# 他のファイルは config.py 経由で設定値を使うので、キーの名前を覚える場所が1か所で済みます。
import os

from dotenv import load_dotenv

# .env ファイルの中身を環境変数として読み込む
load_dotenv()

# LINE公式アカウント（Messaging API）の認証情報
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

# OpenAI APIキー（レシピ文章の生成と画像生成の両方に使う）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# レシピ文章生成に使うモデルと、画像生成に使うモデル
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o")
# gpt-image-1はdall-e-3と違い、画像をURLではなくBase64データで返すため、
# 生成した画像はサーバー内に保存し、そのファイルへのURLをLINEに渡す
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
# 画質（low/medium/high）。highは1枚あたり約35秒かかるため、
# LINEの返信速度を優先してlowを既定値にしている（実測で1枚あたり約13秒）
OPENAI_IMAGE_QUALITY = os.getenv("OPENAI_IMAGE_QUALITY", "low")

# 1人（1つのLINEアカウント）が1日に提案してもらえる回数の上限
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "3"))

# 利用回数を記録しておくファイルの場所
USAGE_FILE_PATH = os.getenv("USAGE_FILE_PATH", "data/usage.json")

# 「他には？」で続きを提案するために、直近のリクエスト内容を記録しておくファイルの場所
CONVERSATION_STATE_FILE_PATH = os.getenv("CONVERSATION_STATE_FILE_PATH", "data/conversation_state.json")

# 生成した画像をLINEから読み込めるようにするための、このサーバー自身の公開URL
# Renderにデプロイすると自動で環境変数 RENDER_EXTERNAL_URL がセットされるので、通常は指定不要
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", os.getenv("RENDER_EXTERNAL_URL", ""))
