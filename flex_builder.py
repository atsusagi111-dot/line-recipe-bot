# レシピの中身（辞書）と画像URLから、LINEの「Flex Message」用のbubble（1枚のカード）を組み立てる係。
# Flex Messageは「見た目をリッチにできるLINEの特別なメッセージ形式」。


def _ingredients_text(ingredients: list[dict]) -> str:
    lines = [f"・{item.get('name', '')}　{item.get('amount', '')}" for item in ingredients]
    return "\n".join(lines) if lines else "（情報なし）"


def _numbered_text(items: list[str]) -> str:
    lines = [f"{i}. {step}" for i, step in enumerate(items, start=1)]
    return "\n".join(lines) if lines else "（情報なし）"


def _bulleted_text(items: list[str]) -> str:
    lines = [f"・{item}" for item in items]
    return "\n".join(lines) if lines else "（情報なし）"


def build_recipe_bubble(recipe: dict, image_url: str, label: str) -> dict:
    """
    recipe: openai_client.generate_recipes() が返す "adult" または "baby" の中身
    image_url: openai_client.generate_image() が返す画像URL
    label: カード上部に出す小さなラベル（例:「大人2人分」「1歳児の離乳食」）

    戻り値: Flex Messageのbubble（辞書）。
    """
    body_contents = [
        {"type": "text", "text": label, "size": "xs", "color": "#888888"},
        {
            "type": "text",
            "text": recipe.get("recipe_name", "レシピ"),
            "weight": "bold",
            "size": "xl",
            "wrap": True,
        },
        {"type": "separator", "margin": "md"},
        {"type": "text", "text": "材料", "weight": "bold", "size": "md", "margin": "md"},
        {
            "type": "text",
            "text": _ingredients_text(recipe.get("ingredients", [])),
            "wrap": True,
            "size": "sm",
        },
        {"type": "text", "text": "作り方", "weight": "bold", "size": "md", "margin": "md"},
        {
            "type": "text",
            "text": _numbered_text(recipe.get("steps", [])),
            "wrap": True,
            "size": "sm",
        },
        {"type": "text", "text": "調理のポイント", "weight": "bold", "size": "md", "margin": "md"},
        {
            "type": "text",
            "text": _bulleted_text(recipe.get("tips", [])),
            "wrap": True,
            "size": "sm",
        },
        {"type": "text", "text": "栄養バランス", "weight": "bold", "size": "md", "margin": "md"},
        {
            "type": "text",
            "text": recipe.get("nutrition", ""),
            "wrap": True,
            "size": "sm",
            "color": "#555555",
        },
    ]

    bubble: dict = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": body_contents,
        },
    }

    if image_url:
        bubble["hero"] = {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
        }

    return bubble
