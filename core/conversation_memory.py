import json
import os
import threading
from pathlib import Path
from datetime import datetime, timezone


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CONVERSATIONS_FILE = (
    DATA_DIR / "conversations.json"
)


# ==========================================================
# SETTINGS
# ==========================================================

MAX_HISTORY_MESSAGES = 12

_file_lock = threading.Lock()


# ==========================================================
# INITIALIZATION
# ==========================================================

def ensure_storage() -> None:
    """
    Создаёт папку data и conversations.json,
    если их ещё нет.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not CONVERSATIONS_FILE.exists():
        CONVERSATIONS_FILE.write_text(
            "{}",
            encoding="utf-8",
        )


# ==========================================================
# LOAD / SAVE
# ==========================================================

def load_conversations() -> dict:
    ensure_storage()

    with _file_lock:
        try:
            text = CONVERSATIONS_FILE.read_text(
                encoding="utf-8"
            ).strip()

            if not text:
                return {}

            data = json.loads(text)

            if isinstance(data, dict):
                return data

        except Exception as error:
            print(
                "Ошибка чтения "
                f"conversations.json: {error}"
            )

    return {}


def save_conversations(
    conversations: dict,
) -> None:
    """
    Сохраняет данные через временный файл,
    чтобы уменьшить риск повреждения JSON.
    """

    ensure_storage()

    temp_file = (
        CONVERSATIONS_FILE.with_suffix(
            ".tmp"
        )
    )

    with _file_lock:
        try:
            temp_file.write_text(
                json.dumps(
                    conversations,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            os.replace(
                temp_file,
                CONVERSATIONS_FILE,
            )

        except Exception as error:
            print(
                "Ошибка сохранения "
                f"conversations.json: {error}"
            )


# ==========================================================
# INTERNAL HELPERS
# ==========================================================

def get_timestamp() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def ensure_conversation(
    conversations: dict,
    client_id: str,
    instagram_user_id: str,
) -> dict:

    client_id = str(
        client_id
    ).strip()

    instagram_user_id = str(
        instagram_user_id
    ).strip()

    if client_id not in conversations:
        conversations[client_id] = {}

    client_conversations = (
        conversations[client_id]
    )

    if instagram_user_id not in (
        client_conversations
    ):
        client_conversations[
            instagram_user_id
        ] = {
            "current_product": None,
            "history": [],
            "state": None,
            "updated_at": get_timestamp(),
        }

    return client_conversations[
        instagram_user_id
    ]


# ==========================================================
# GET FULL MEMORY
# ==========================================================

def get_memory(
    client_id: str,
    instagram_user_id: str,
) -> dict:

    conversations = load_conversations()

    memory = ensure_conversation(
        conversations,
        client_id,
        instagram_user_id,
    )

    return memory


# ==========================================================
# CURRENT PRODUCT
# ==========================================================

def get_current_product(
    client_id: str,
    instagram_user_id: str,
) -> dict | None:

    memory = get_memory(
        client_id,
        instagram_user_id,
    )

    product = memory.get(
        "current_product"
    )

    if isinstance(product, dict):
        return product

    return None


def set_current_product(
    client_id: str,
    instagram_user_id: str,
    product: dict | None,
) -> None:

    conversations = load_conversations()

    memory = ensure_conversation(
        conversations,
        client_id,
        instagram_user_id,
    )

    memory["current_product"] = product
    memory["updated_at"] = get_timestamp()

    save_conversations(
        conversations
    )


def clear_current_product(
    client_id: str,
    instagram_user_id: str,
) -> None:

    set_current_product(
        client_id=client_id,
        instagram_user_id=instagram_user_id,
        product=None,
    )


# ==========================================================
# CONVERSATION STATE
# ==========================================================

def get_state(
    client_id: str,
    instagram_user_id: str,
) -> str | None:

    memory = get_memory(
        client_id,
        instagram_user_id,
    )

    state = memory.get(
        "state"
    )

    if state:
        return str(state)

    return None


def set_state(
    client_id: str,
    instagram_user_id: str,
    state: str | None,
) -> None:

    conversations = load_conversations()

    memory = ensure_conversation(
        conversations,
        client_id,
        instagram_user_id,
    )

    memory["state"] = state
    memory["updated_at"] = get_timestamp()

    save_conversations(
        conversations
    )


def clear_state(
    client_id: str,
    instagram_user_id: str,
) -> None:

    set_state(
        client_id=client_id,
        instagram_user_id=instagram_user_id,
        state=None,
    )


# ==========================================================
# MESSAGE HISTORY
# ==========================================================

def add_message(
    client_id: str,
    instagram_user_id: str,
    role: str,
    text: str,
) -> None:

    text = (
        text or ""
    ).strip()

    if not text:
        return

    conversations = load_conversations()

    memory = ensure_conversation(
        conversations,
        client_id,
        instagram_user_id,
    )

    history = memory.get(
        "history"
    )

    if not isinstance(history, list):
        history = []

    history.append(
        {
            "role": role,
            "text": text,
            "timestamp": get_timestamp(),
        }
    )

    # Храним только последние сообщения,
    # чтобы память не росла бесконечно.
    history = history[
        -MAX_HISTORY_MESSAGES:
    ]

    memory["history"] = history
    memory["updated_at"] = get_timestamp()

    save_conversations(
        conversations
    )


def get_history(
    client_id: str,
    instagram_user_id: str,
) -> list[dict]:

    memory = get_memory(
        client_id,
        instagram_user_id,
    )

    history = memory.get(
        "history",
        [],
    )

    if isinstance(history, list):
        return history

    return []


# ==========================================================
# CONTEXT FOR OPENAI
# ==========================================================

def get_conversation_context(
    client_id: str,
    instagram_user_id: str,
) -> str:

    history = get_history(
        client_id,
        instagram_user_id,
    )

    if not history:
        return ""

    lines = []

    for item in history:
        role = item.get(
            "role",
            ""
        )

        text = item.get(
            "text",
            ""
        )

        if not text:
            continue

        if role == "user":
            label = "Клиент"

        elif role == "assistant":
            label = "Ассистент"

        else:
            label = role

        lines.append(
            f"{label}: {text}"
        )

    return "\n".join(
        lines
    )


# ==========================================================
# CLEAR CONVERSATION
# ==========================================================

def clear_conversation(
    client_id: str,
    instagram_user_id: str,
) -> None:

    conversations = load_conversations()

    client_data = conversations.get(
        client_id
    )

    if not isinstance(
        client_data,
        dict,
    ):
        return

    client_data.pop(
        str(instagram_user_id),
        None,
    )

    save_conversations(
        conversations
    )