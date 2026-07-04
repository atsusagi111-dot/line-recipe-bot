# 「1人1日3回まで」という利用回数の制限を管理する係。
# シンプルに、JSONファイルに「ユーザーID / 日付 / 回数」を保存するだけの仕組み。
# 本番用の本格的なデータベースではないが、個人〜小規模利用なら十分。
import json
import os
import threading
from datetime import date

import config

# 同時に複数のリクエストが来てもファイルが壊れないようにする鍵（ロック）
_lock = threading.Lock()


def _load() -> dict:
    if not os.path.exists(config.USAGE_FILE_PATH):
        return {}
    try:
        with open(config.USAGE_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # 万が一ファイルが壊れていても、アプリ全体を止めずに空データから再開する
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(config.USAGE_FILE_PATH) or ".", exist_ok=True)
    with open(config.USAGE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_and_increment(user_id: str) -> tuple[bool, int]:
    """
    ユーザーが今日まだ提案を受け取れるかを確認し、OKなら利用回数を1つ増やす。

    戻り値:
        (利用してよいか, 増やした後の残り回数)
    """
    today = date.today().isoformat()

    with _lock:
        data = _load()
        record = data.get(user_id)

        if record is None or record.get("date") != today:
            # 記録が無い、または日付が変わっていたらリセット
            record = {"date": today, "count": 0}

        if record["count"] >= config.DAILY_LIMIT:
            data[user_id] = record
            _save(data)
            return False, 0

        record["count"] += 1
        data[user_id] = record
        _save(data)

        remaining = config.DAILY_LIMIT - record["count"]
        return True, remaining
