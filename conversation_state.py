# 「他には？」と聞かれた時に、直前と同じ食材・調味料で再提案できるようにするための係。
# ユーザーごとに「直近リクエストした食材・調味料」と「提案済みのレシピ名」をJSONファイルに保存しておく。
import json
import os
import threading

import config

# 同時に複数のリクエストが来てもファイルが壊れないようにする鍵（ロック）
_lock = threading.Lock()

# 1ユーザーあたり、重複チェック用に保持しておくレシピ名の最大件数
# （長時間「他には？」を繰り返してもプロンプトが際限なく長くならないようにする）
_MAX_RECIPE_NAMES = 8


def _load() -> dict:
    if not os.path.exists(config.CONVERSATION_STATE_FILE_PATH):
        return {}
    try:
        with open(config.CONVERSATION_STATE_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # 万が一ファイルが壊れていても、アプリ全体を止めずに空データから再開する
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(config.CONVERSATION_STATE_FILE_PATH) or ".", exist_ok=True)
    with open(config.CONVERSATION_STATE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_last_request(user_id: str) -> dict | None:
    """
    直前にそのユーザーがリクエストした内容を取得する。
    無ければ None（＝「他には？」と言われても続きが無い状態）。
    """
    with _lock:
        return _load().get(user_id)


def save_request(user_id: str, ingredients: list[str], seasonings: list[str]) -> None:
    """新しい食材・調味料でリクエストされた時に呼び出し、提案済みレシピ名をリセットする"""
    with _lock:
        data = _load()
        data[user_id] = {
            "ingredients": ingredients,
            "seasonings": seasonings,
            "recipe_names": {"adult": [], "baby": []},
        }
        _save(data)


def add_recipe_names(user_id: str, recipe_names: dict[str, str]) -> None:
    """今回提案したレシピ名（adult/baby）を、既出リストに追加しておく"""
    with _lock:
        data = _load()
        record = data.get(user_id)
        if record is None:
            return

        names = record.setdefault("recipe_names", {"adult": [], "baby": []})
        for key, name in recipe_names.items():
            if not name:
                continue
            bucket = names.setdefault(key, [])
            bucket.append(name)
            del bucket[:-_MAX_RECIPE_NAMES]

        data[user_id] = record
        _save(data)
