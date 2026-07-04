# このファイルがアプリの本体（入口）です。
# LINEから届いたメッセージを受け取り → 内容を解析 → レシピと画像を生成 → LINEに返信する、
# という一連の流れをここでつなぎ合わせています。
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, abort, request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    FlexContainer,
    FlexMessage,
    MessagingApi,
    PushMessageRequest,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import config
import flex_builder
import message_parser
import openai_client
import usage_limiter

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

line_config = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)


@app.route("/", methods=["GET"])
def health_check():
    """Renderの死活監視やブラウザ確認用の簡単な応答"""
    return "LINE recipe bot is running."


@app.route("/callback", methods=["POST"])
def callback():
    """LINEプラットフォームがメッセージ受信のたびに呼び出すURL（Webhook）"""
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # LINEチャネルシークレットが間違っている場合など、署名が一致しない時
        abort(400)

    return "OK"


def _reply(reply_token: str, text: str) -> None:
    with ApiClient(line_config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        )


def _push_recipes(user_id: str, recipes: dict) -> None:
    """adult/babyそれぞれの画像を生成し、Flex Messageとしてまとめて送信する"""
    labels = {"adult": "👨‍👩‍👧 大人2人分", "baby": "🍼 1歳児の離乳食"}
    keys = ("adult", "baby")

    # 画像生成は1枚十数秒かかるため、2枚を同時に生成して待ち時間を半分にする
    with ThreadPoolExecutor(max_workers=2) as executor:
        image_urls = list(
            executor.map(
                lambda key: openai_client.generate_image(
                    recipes[key].get("image_prompt", recipes[key].get("recipe_name", ""))
                ),
                keys,
            )
        )

    messages = []
    for key, image_url in zip(keys, image_urls):
        recipe = recipes[key]
        bubble = flex_builder.build_recipe_bubble(recipe, image_url, labels[key])
        messages.append(
            FlexMessage(
                alt_text=f"{labels[key]}：{recipe.get('recipe_name', 'レシピ')}",
                contents=FlexContainer.from_json(json.dumps(bubble)),
            )
        )

    with ApiClient(line_config) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(to=user_id, messages=messages)
        )


def _generate_and_push(user_id: str, ingredients: list, seasonings: list) -> None:
    """時間のかかるAI生成処理をバックグラウンドで行い、終わったらLINEにプッシュ送信する"""
    try:
        recipes = openai_client.generate_recipes(ingredients, seasonings)
        _push_recipes(user_id, recipes)
    except Exception:
        # Renderのログに実際のエラー内容を残す（原因調査用）
        logger.exception("レシピ生成またはLINE送信中にエラーが発生しました")
        with ApiClient(line_config) as api_client:
            MessagingApi(api_client).push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[
                        TextMessage(
                            text="申し訳ありません、レシピの生成中にエラーが発生しました。少し時間をおいて、もう一度お試しください。"
                        )
                    ],
                )
            )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent) -> None:
    user_id = event.source.user_id
    text = event.message.text

    parsed = message_parser.parse_input(text)
    if parsed is None:
        _reply(event.reply_token, message_parser.USAGE_TEXT)
        return

    allowed, remaining = usage_limiter.check_and_increment(user_id)
    if not allowed:
        _reply(
            event.reply_token,
            f"本日の提案回数（{config.DAILY_LIMIT}回まで）に達しました。また明日お試しください🙏",
        )
        return

    # GPT-4oでの文章生成とgpt-image-1での画像生成には時間がかかる（数十秒）ため、
    # 先に「受け付けました」だけ即返信し、本処理は裏側（別スレッド）で進めてから
    # 出来上がり次第プッシュ通知でレシピを送る、という2段階の流れにしている。
    _reply(
        event.reply_token,
        f"🍳 レシピを考えています…30秒ほどお待ちください！（本日の残り提案回数: {remaining}回）",
    )
    threading.Thread(
        target=_generate_and_push,
        args=(user_id, parsed["ingredients"], parsed["seasonings"]),
        daemon=True,
    ).start()


if __name__ == "__main__":
    app.run(port=5000)
