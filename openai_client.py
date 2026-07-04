# OpenAIのAPIを使って「レシピ文章の生成」と「料理イメージ画像の生成」を行う係。
# ・レシピ文章 → GPT-4o に JSON形式で出力してもらう
# ・イメージ画像 → gpt-image-1 で生成する
#   （gpt-image-1はURLではなくBase64データで画像を返すため、
#    このサーバーのstaticフォルダにファイルとして保存し、そのURLをLINEに渡す）
import base64
import json
import os
import random
import uuid

from openai import OpenAI

import config

_STATIC_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "static", "generated")

_client = OpenAI(api_key=config.OPENAI_API_KEY)

# GPT-4oに渡すシステムプロンプト（AIへの役割・ルール説明）
_SYSTEM_PROMPT = """あなたは2つの顔を持つ専門家です。
・大人用レシピについては、家庭で「ご飯がすすむ」と思えるくらい美味しい絶品料理を作る、経験豊富なプロの料理人。
・離乳食レシピについては、月齢ごとの適切な形状・味付けを熟知した離乳食の専門家（管理栄養士）。

必ず守るルール:
1. 食材（主材料）は、ユーザーが入力したものだけに限定すること。入力に無い食材を追加しない
   （例外として、茹でる・煮る際の「水」「だし汁（水+顆粒だし程度）」は使ってよい）。
2. 調味料については:
   - ユーザーが調味料を指定した場合は、その中から選んで使うこと（指定された調味料をすべて使い切る必要はない）。
   - ユーザーが調味料を1つも指定しなかった場合は、料理人・栄養士としての判断で、家庭に常備されている
     基本的な調味料（塩、こしょう、醤油、みりん、酒、砂糖、味噌、酢、サラダ油、ごま油、顆粒だしなど）の中から
     自由に選んでよい。「味付けなし」は絶対に避け、必ず何らかの調味料で味を決めること。
   - 調味料は必ずingredients（材料）に分量付きで含めること（例: {"name": "醤油", "amount": "大さじ1"}）。
3. 調理時間は20〜30分以内で完成すること。
4. 大人2人分のレシピ（adult）と、1歳児向けの離乳食レシピ（baby）の2つを提案すること。
5. 調味料の分量:
   - adult（大人用）: 白いご飯が進むような、コクや旨味をしっかり感じる濃さ・分量にすること（例: 大さじ1、小さじ1/2など具体的に）。
   - baby（1歳児用）: 大人用より明らかに薄味にすること。塩分・糖分は最小限（「ごく少量」「小さじ1/4」など）。はちみつは絶対に使用しないこと。
6. steps（手順）の中に「煮る」「茹でる」「炒める」「蒸す」「炊く」など時間のかかる工程がある場合は、必ず「弱火で5分煮る」のように具体的な時間を明記すること。
7. babyのレシピの形状（食感）について、1歳児は「離乳食完了期」であり、なめらかなペースト状（ポタージュ状）は5〜8ヶ月向けの離乳食初期〜中期の形状であって1歳児には適さない。
   - 基本は「歯茎で噛める柔らかさの、食べやすい小さめの一口大」を標準の形状とすること。
   - 切り方は食材本来の形を活かした自然な切り方（乱切り、いちょう切り、半月切り、そぎ切り、粗みじん切りなど）を選び、
     さいの目切りのような「均一な正方形・立方体」には絶対にしないこと（不自然に見えるため）。
   - すりつぶす・ペースト状にする・裏ごしするといった工程は、繊維が硬く1歳児には噛み切りにくい食材（例: 筋の多い葉物など）を使う場合にのみ、必要な範囲で選択すること。むやみにペースト状にしない。
   - 選んだ切り方は必ずstepsの中に具体的な工程として明記すること（例:「いちょう切りにする」「そぎ切りにして小さくする」など）。
8. image_prompt（画像生成AI用の英語プロンプト）は、実際にstepsを行った結果としてできあがる見た目・食感と完全に一致させ、かつ写実的であること。
   - stepsでペースト状にする／すりつぶす／裏ごしする工程がある場合のみ、image_promptに"smooth pureed"のような表現を使うこと。
   - それ以外の場合は、"pureed"や"paste"、"smooth"という表現は使わないこと。
   - 食材は日本のスーパーで売られている実物の色・厚み・自然な切り口で描写すること
     （例: 人参は乱切りやいちょう切りでオレンジ色の自然な断面、じゃがいもは皮を剥いた淡い黄色の不揃いな塊、
     豚肉や鶏肉は厚みのある一口大の欠片、魚は切り身や自然にほぐれた身など）。
   - "perfectly uniform cubes", "square-shaped", "diced into identical squares" のような、不自然に均一な立方体・正方形を
     連想させる表現は絶対に使わないこと。代わりに"irregular, hand-cut, natural bite-sized pieces"のような
     自然さを強調する表現を使うこと。
9. 大人用（adult）レシピは、こってり濃い味の料理（甘辛だれ、揚げ物、こってり炒め物など）ばかりに偏らないこと。
   ユーザーメッセージ内で指定された今回の味の方向性（こってり系／さっぱり・ヘルシー系）に従い、
   さっぱり系が指定された場合は、蒸す・茹でる・和える・煮浸しにするなどの調理法や、ポン酢・レモン・酢・薬味・
   出汁を使ったさっぱりした味付けを選び、油や糖分を控えめにすること。
10. 出力は必ず指定のJSON形式のみで、余計な説明文を含めないこと。

出力するJSONの形式（この構造に厳密に従うこと）:
{
  "adult": {
    "recipe_name": "料理名",
    "ingredients": [{"name": "食材名または調味料名", "amount": "分量"}],
    "steps": ["手順1（時間のかかる工程は分数を明記）", "手順2", "..."],
    "tips": ["調理のポイント（1〜2個）"],
    "nutrition": "栄養バランスの説明（100文字程度、日本語）",
    "image_prompt": "完成した料理を描写する英語のプロンプト（画像生成AI用、stepsの結果と一致させる）"
  },
  "baby": {
    "recipe_name": "料理名",
    "ingredients": [{"name": "食材名または調味料名", "amount": "分量"}],
    "steps": ["手順1（時間のかかる工程は分数を明記、食感を変える加工があれば明記）", "手順2", "..."],
    "tips": ["調理のポイント（1〜2個）"],
    "nutrition": "栄養バランスの説明（100文字程度、日本語）",
    "image_prompt": "完成した離乳食を描写する英語のプロンプト（画像生成AI用、stepsの結果と一致させる）"
  }
}
"""


# 大人用レシピの味の方向性。こってり系に偏らないよう、2〜3回に1回程度の割合で
# さっぱり・ヘルシー系が選ばれるようにする（weightsで重み付け）
_ADULT_STYLES = [
    ("こってり・満足感重視（甘辛だれ、照り焼き、揚げ焼き、こってり炒めなど、しっかりした濃い味）", 60),
    ("さっぱり・ヘルシー系（蒸す、茹でる、和える、煮浸しなど。ポン酢・レモン・酢・薬味・出汁を活かし、油や糖分は控えめ）", 40),
]


def generate_recipes(ingredients: list[str], seasonings: list[str]) -> dict:
    """
    食材・調味料のリストから、大人用レシピと離乳食レシピをまとめて生成する。

    戻り値: {"adult": {...}, "baby": {...}} という辞書（_SYSTEM_PROMPT のJSON形式）
    """
    seasoning_text = (
        "、".join(seasonings)
        if seasonings
        else "（指定なし。家庭の基本的な調味料の中から、プロとして最適なものを自由に選んで味を決めてください）"
    )
    styles, weights = zip(*_ADULT_STYLES)
    adult_style = random.choices(styles, weights=weights, k=1)[0]

    user_prompt = (
        f"食材: {'、'.join(ingredients)}\n"
        f"調味料: {seasoning_text}\n"
        f"今回のadult（大人用）レシピの味の方向性: {adult_style}\n\n"
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
        quality=config.OPENAI_IMAGE_QUALITY,
        n=1,
    )
    image_bytes = base64.b64decode(response.data[0].b64_json)

    os.makedirs(_STATIC_IMAGE_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    with open(os.path.join(_STATIC_IMAGE_DIR, filename), "wb") as f:
        f.write(image_bytes)

    return f"{config.PUBLIC_BASE_URL.rstrip('/')}/static/generated/{filename}"
