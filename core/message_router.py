import json
import re
from pathlib import Path

from core.ai_service import (
    generate_ai_response,
    generate_web_response,
)
from core.client_registry import get_client


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENTS_DIR = BASE_DIR / "clients"


# ==========================================================
# ROUTES
# ==========================================================

ROUTE_PRODUCT = "product"
ROUTE_AI = "ai"
ROUTE_WEB = "web"
ROUTE_HANDOFF = "handoff"


# ==========================================================
# PHRASES
# ==========================================================

HANDOFF_PHRASES = {
    "хочу заказать",
    "хочу купить",
    "оформить заказ",
    "хочу оформить заказ",
    "позовите менеджера",
    "позвать менеджера",
    "менеджер",
    "живой человек",
    "оператор",
    "vreau sa comand",
    "vreau să comand",
    "vreau sa cumpar",
    "vreau să cumpăr",
    "manager",
    "operator",
}


# Вопросы, для которых часто нужна
# актуальная информация из интернета.
WEB_CUES = {
    "сколько лет",
    "когда открыл",
    "когда открыли",
    "когда основан",
    "когда основана",
    "кто основал",
    "кто владелец",
    "кто основатель",
    "официальный сайт",
    "какие филиалы",
    "сколько филиалов",
    "где находятся",
    "какие бренды представлены",
    "какие бренды у вас",
    "последние новости",
    "сейчас работает",
    "актуальное расписание",
    "program actual",
    "cand s-a deschis",
    "când s-a deschis",
    "cine a fondat",
    "cate filiale",
    "câte filiale",
}


# ==========================================================
# TEXT HELPERS
# ==========================================================

def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def contains_any(
    text: str,
    phrases: set[str],
) -> bool:
    return any(
        phrase in text
        for phrase in phrases
    )


# ==========================================================
# LOAD PRODUCTS
# ==========================================================

def load_client_products(
    client_id: str,
) -> list[dict]:

    client_config = get_client(
        client_id
    )

    if client_config is None:
        return []

    client_folder = client_config[
        "folder"
    ]

    products_path = (
        CLIENTS_DIR
        / client_folder
        / "products.json"
    )

    if not products_path.exists():
        return []

    try:
        with products_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except Exception as error:
        print(
            f"Ошибка чтения products.json "
            f"для {client_id}: {error}"
        )
        return []

    # Поддерживаем сразу несколько форматов JSON.
    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        if isinstance(
            data.get("products"),
            list,
        ):
            return data["products"]

        if isinstance(
            data.get("items"),
            list,
        ):
            return data["items"]

    return []


# ==========================================================
# PRODUCT SEARCH
# ==========================================================

def get_product_search_values(
    product: dict,
) -> list[str]:

    values = []

    important_keys = (
        "name",
        "article",
        "sku",
        "code",
        "url",
        "link",
        "title",
    )

    for key in important_keys:
        value = product.get(key)

        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()

            if value:
                values.append(value)

    return values


def find_product_in_message(
    products: list[dict],
    message: str,
) -> dict | None:

    message_normalized = normalize_text(
        message
    )

    if not message_normalized:
        return None

    best_product = None
    best_score = 0

    for product in products:

        values = get_product_search_values(
            product
        )

        score = 0

        for value in values:
            value_normalized = normalize_text(
                value
            )

            if not value_normalized:
                continue

            # Полное совпадение значения
            # внутри сообщения.
            if value_normalized in message_normalized:
                score += 10

            # Разбиваем название на слова,
            # чтобы находить товар даже
            # при неполном названии.
            words = [
                word
                for word in re.findall(
                    r"[a-zа-яё0-9]+",
                    value_normalized,
                    flags=re.IGNORECASE,
                )
                if len(word) >= 3
            ]

            matched_words = sum(
                1
                for word in words
                if word in message_normalized
            )

            score += matched_words

        if score > best_score:
            best_score = score
            best_product = product

    # Чтобы случайное одно слово
    # не определяло товар ошибочно.
    if best_score < 2:
        return None

    return best_product


# ==========================================================
# PRODUCT CONTEXT FOR GPT
# ==========================================================

def product_to_context(
    product: dict | None,
) -> str:

    if not product:
        return ""

    lines = []

    for key, value in product.items():

        if value in (
            None,
            "",
            [],
            {},
        ):
            continue

        if isinstance(
            value,
            (dict, list),
        ):
            value = json.dumps(
                value,
                ensure_ascii=False,
            )

        lines.append(
            f"{key}: {value}"
        )

    return "\n".join(lines)


# ==========================================================
# BUSINESS CONTEXT
# ==========================================================

def get_business_context(
    client_id: str,
) -> str:

    client_config = get_client(
        client_id
    )

    if client_config is None:
        return ""

    client_name = client_config.get(
        "name",
        client_id,
    )

    return (
        f"Название бизнеса: {client_name}"
    )


# ==========================================================
# ROUTE DETECTION
# ==========================================================

def detect_route(
    message: str,
    product: dict | None,
) -> str:

    normalized = normalize_text(
        message
    )

    # ------------------------------------------
    # HANDOFF
    # ------------------------------------------

    if contains_any(
        normalized,
        HANDOFF_PHRASES,
    ):
        return ROUTE_HANDOFF

    # ------------------------------------------
    # WEB
    # ------------------------------------------

    if contains_any(
        normalized,
        WEB_CUES,
    ):
        return ROUTE_WEB

    # ------------------------------------------
    # PRODUCT
    # ------------------------------------------

    if product is not None:
        return ROUTE_PRODUCT

    # ------------------------------------------
    # DEFAULT AI
    # ------------------------------------------

    return ROUTE_AI


# ==========================================================
# MAIN ROUTER
# ==========================================================

def route_message(
    client_id: str,
    message: str,
    current_product: dict | None = None,
    conversation_context: str = "",
) -> dict:

    message = (
        message or ""
    ).strip()

    if not message:
        return {
            "route": ROUTE_AI,
            "answer": "",
            "product": current_product,
        }

    client_config = get_client(
        client_id
    )

    if client_config is None:
        return {
            "route": "error",
            "answer": (
                "Не удалось определить "
                "настройки бизнеса."
            ),
            "product": None,
        }

    # ======================================================
    # PRODUCTS
    # ======================================================

    products = load_client_products(
        client_id
    )

    explicit_product = (
        find_product_in_message(
            products,
            message,
        )
    )

    if explicit_product is not None:
        product = explicit_product

    else:
        product = current_product

    # ======================================================
    # DETECT ROUTE
    # ======================================================

    route = detect_route(
        message=message,
        product=product,
    )

    business_context = (
        get_business_context(
            client_id
        )
    )

    product_context = (
        product_to_context(
            product
        )
    )

    # ======================================================
    # MANAGER
    # ======================================================

    if route == ROUTE_HANDOFF:

        client_name = client_config[
            "name"
        ]

        answer = (
            "Конечно 🤍 "
            f"Я передам ваш запрос "
            f"сотруднику {client_name}."
        )

        return {
            "route": route,
            "answer": answer,
            "product": product,
            "handoff": True,
        }

    # ======================================================
    # WEB SEARCH
    # ======================================================

    if route == ROUTE_WEB:

        answer = generate_web_response(
            client_id=client_id,
            user_message=message,
            business_context=business_context,
        )

        return {
            "route": route,
            "answer": answer,
            "product": product,
            "handoff": False,
        }

    # ======================================================
    # PRODUCT + AI
    # ======================================================

    if route == ROUTE_PRODUCT:

        answer = generate_ai_response(
            client_id=client_id,
            user_message=message,
            product_context=product_context,
            business_context=business_context,
            conversation_context=(
                conversation_context
            ),
        )

        return {
            "route": route,
            "answer": answer,
            "product": product,
            "handoff": False,
        }

    # ======================================================
    # GENERAL AI
    # ======================================================

    answer = generate_ai_response(
        client_id=client_id,
        user_message=message,
        business_context=business_context,
        conversation_context=(
            conversation_context
        ),
    )

    return {
        "route": ROUTE_AI,
        "answer": answer,
        "product": product,
        "handoff": False,
    }