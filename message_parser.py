# LINEから届いたテキストメッセージを「食材リスト」と「調味料リスト」に分解する係。
# ユーザーには次のような形式で送ってもらう想定です。
#
#   食材：豚肉、キャベツ、人参
#   調味料：醤油、みりん
#
# 「調味料」の行は無くてもOK（必須ではない）。
import re

# 使い方を説明するメッセージ（入力形式が読み取れなかった時に返す）
USAGE_TEXT = (
    "🍳 使い方\n"
    "次のように送ってください。\n\n"
    "食材：豚肉、キャベツ、人参\n"
    "調味料：醤油、みりん\n\n"
    "※調味料は無くても大丈夫です。\n"
    "※食材は、、（読点）やカンマ、スペースで区切ってください。"
)

_LABEL_INGREDIENT = re.compile(r"^\s*食材\s*[:：]\s*(.*)$")
_LABEL_SEASONING = re.compile(r"^\s*調味料\s*[:：]\s*(.*)$")
# 「、」「,」「，」「・」および半角/全角スペースを区切り文字として扱う
_SPLIT_PATTERN = re.compile(r"[、,，・\s]+")


def _split_items(raw: str) -> list[str]:
    """カンマや読点で区切られた文字列を、空要素を除いたリストに変換する"""
    items = [item.strip() for item in _SPLIT_PATTERN.split(raw)]
    return [item for item in items if item]


def parse_input(text: str) -> dict | None:
    """
    LINEメッセージのテキストを解析する。

    戻り値:
        {"ingredients": [...], "seasonings": [...]} を返す。
        食材が1つも読み取れなかった場合は None を返す（＝入力形式エラー）。
    """
    ingredients: list[str] = []
    seasonings: list[str] = []
    found_label = False

    for line in text.splitlines():
        m_ingredient = _LABEL_INGREDIENT.match(line)
        m_seasoning = _LABEL_SEASONING.match(line)
        if m_ingredient:
            found_label = True
            ingredients.extend(_split_items(m_ingredient.group(1)))
        elif m_seasoning:
            found_label = True
            seasonings.extend(_split_items(m_seasoning.group(1)))

    # 「食材：」のラベルが無い場合は、メッセージ全体を食材リストとして扱う（初心者向けの救済処置）
    if not found_label:
        ingredients = _split_items(text)

    if not ingredients:
        return None

    return {"ingredients": ingredients, "seasonings": seasonings}
