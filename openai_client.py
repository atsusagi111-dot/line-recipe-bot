# OpenAIのAPIを使って「レシピ文章の生成」と「料理イメージ画像の生成」を行う係。
# ・レシピ文章 → GPT-4o に JSON形式で出力してもらう
# ・イメージ画像 → gpt-image-1 で生成する
#   （gpt-image-1はURLではなくBase64データで画像を返すため、
#    このサーバーのstaticフォルダにファイルとして保存し、そのURLをLINEに渡す）
import base64
import json
import os
import uuid

from openai import OpenAI

import config

_STATIC_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "static", "generated")

_client = OpenAI(api_key=config.OPENAI_API_KEY)

# GPT-4oに渡すシステムプロンプト（AIへの役割・ルール説明）
_SYSTEM_PROMPT = """あなたは経験豊富なプロの料理人です。
ユーザーから渡された食材と調味料だけを使い、家庭で「ご飯がすすむ」と思えるくらい美味しい絶品料理を提案してください。

必ず守るルール:
1. 使う食材・調味料は、ユーザーが入力したものだけに限定すること。入力に無いものを追加しない（例外として、茹でる・煮る際の「水」だけは使ってよい）。
2. 調理時間は20〜30分以内で完成すること。
3. 大人2人分のレシピ（adult）と、1歳児向けの離乳食レシピ（baby）の2つを提案すること。
4. babyのレシピは、大人用と同じ食材の中から、1歳児が食べても安全なように調整すること
   （はちみつは1歳未満に厳禁、塩分・糖分は控えめ、飲み込みやすいように細かく刻む・柔らかく煮るなど食感を配慮する）。
5. 出力は必ず指定のJSON形式のみで、余計な説明文を含めないこと。

出力するJSONの形式（この構造に厳密に従うこと）:
{
  "adult": {
    "recipe_name": "料理名",
    "ingredients": [{"name": "食材名", "amount": "分量"}],
    "steps": ["手順1", "手順2", "..."],
    "tips": ["調理のポイント（1〜2個）"],
    "nutrition": "栄養バランスの説明（100文字程度、日本語）",
    "image_prompt": "完成した料理を描写する英語のプロンプト（画像生成AI用）"
  },
  "baby": {
    "recipe_name": "料理名",
    "ingredients": [{"name": "食材名", "amount": "分量"}],
    "steps": ["手順1", "手順2", "..."],
    "tips": ["調理のポイント（1〜2個）"],
    "nutrition": "栄養バランスの説明（100文字程度、日本語）",
    "image_prompt": "完成した離乳食を描写する英語のプロンプト（画像生成AI用）"
  }
}
"""


def generate_recipes(ingredients: list[str], seasonings: list[str]) -> dict:
    """
    食材・調味料のリストから、大人用レシピと離乳食レシピをまとめて生成する。

    戻り値: {"adult": {...}, "baby": {...}} という辞書（_SYSTEM_PROMPT のJSON形式）
    """
    seasoning_text = "、".join(seasonings) if seasonings else "（指定なし。調味料は使わない、または食材のみで完結させる）"
    user_prompt = (
        f"食材: {'、'.join(ingredients)}\n"
        f"調味料: {seasoning_text}\n\n"
        "上記のルールに従い、大人2人分のレシピと1歳児向け離乳食レシピをJSONで出力してください。"
    )

    response = _client.chat.completions.create(
        model=config.OPENAI_TEXT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )

    content = response.choices[0].message.content
    return json.loads(content)


def generate_image(image_prompt: str) -> str:
    """
    料理の説明文（英語プロンプト）から、gpt-image-1で画像を生成する。
    生成された画像（Base64）をファイルとして保存し、LINEから読み込める公開URLを返す。
    PUBLIC_BASE_URLが設定されていない場合は、画像なし（空文字）として扱う。
    """
    if not config.PUBLIC_BASE_URL:
        return ""

    response = _client.images.generate(
        model=config.OPENAI_IMAGE_MODEL,
        prompt=image_prompt,
        size="1024x1024",
        n=1,
    )
    image_bytes = base64.b64decode(response.data[0].b64_json)

    os.makedirs(_STATIC_IMAGE_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    with open(os.path.join(_STATIC_IMAGE_DIR, filename), "wb") as f:
        f.write(image_bytes)

    return f"{config.PUBLIC_BASE_URL.rstrip('/')}/static/generated/{filename}"
