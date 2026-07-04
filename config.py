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
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")

# 1人（1つのLINEアカウント）が1日に提案してもらえる回数の上限
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "3"))

# 利用回数を記録しておくファイルの場所
USAGE_FILE_PATH = os.getenv("USAGE_FILE_PATH", "data/usage.json")
