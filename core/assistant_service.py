import re

from core.conversation_memory import (
    add_message,
    clear_state,
    get_conversation_context,
    get_current_product,
    get_state,
    set_current_product,
    set_state,
    start_new_product_context,
)

from core.message_router import (
    find_product_in_message,
    load_client_products,
    route_message,
)


STATE_WAITING_FOR_DELIVERY_CITY = (
    "waiting_for_delivery_city"
)


DELIVERY_CUES = {
    "доставка",
    "доставляете",
    "доставить",
    "доставку",
    "livrare",
    "livrarea",
    "livrati",
    "livrați",
    "delivery",
}


PRODUCT_REFERENCE_CUES = {
    "он",
    "она",
    "оно",
    "они",
    "его",
    "ее",
    "её",
    "их",
    "этот",
    "эта",
    "это",
    "эти",
    "такой",
    "такая",
    "такое",
    "такие",
    "el",
    "ea",
    "acesta",
    "aceasta",
    "acestea",
    "it",
    "this",
    "that",
    "these",
    "those",
}


PRODUCT_QUESTION_CUES = {
    "цена",
    "стоит",
    "стоимость",
    "размер",
    "размеры",
    "цвет",
    "цвета",
    "наличие",
    "в наличии",
    "материал",
    "состав",
    "pret",
    "preț",
    "costa",
    "costă",
    "marime",
    "mărime",
    "culoare",
    "disponibil",
    "price",
    "cost",
    "size",
    "color",
    "colour",
    "available",
    "availability",
    "material",
}


# ==========================================================
# TEXT HELPERS
# ==========================================================

def normalize_text(
    text: str,
) -> str:

    text = (
        text or ""
    ).lower().strip()

    return re.sub(
        r"\s+",
        " ",
        text,
    )


def extract_url(
    text: str,
) -> str | None:

    match = re.search(
        r"https?://[^\s]+",
        text or "",
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return None


def get_text_without_url(
    message: str,
) -> str:

    url = extract_url(
        message
    )

    if not url:
        return message.strip()

    return (
        message
        .replace(
            url,
            " ",
        )
        .strip(
            " \t\r\n-–—"
        )
    )


def is_link_only(
    message: str,
) -> bool:

    url = extract_url(
        message
    )

    if not url:
        return False

    text_without_url = (
        get_text_without_url(
            message
        )
    )

    return not bool(
        text_without_url
    )


def contains_any(
    text: str,
    phrases: set[str],
) -> bool:

    return any(
        phrase in text
        for phrase in phrases
    )


# ==========================================================
# PRODUCT HELPERS
# ==========================================================

def get_product_article(
    product: dict,
) -> str:

    possible_keys = (
        "article",
        "product_code",
        "code",
        "id",
    )

    for key in possible_keys:

        value = product.get(
            key
        )

        if value is not None:

            return str(
                value
            ).strip()

    return ""


def find_product_by_article(
    client_id: str,
    article: str,
) -> dict | None:
    """
    Находит полный объект товара в products.json
    по внутреннему артикулу Vision.
    """

    article = str(
        article or ""
    ).strip()

    if not article:
        return None

    products = (
        load_client_products(
            client_id
        )
    )

    for product in products:

        if not isinstance(
            product,
            dict,
        ):
            continue

        product_article = (
            get_product_article(
                product
            )
        )

        if (
            product_article
            == article
        ):
            return product

    return None


def sanitize_answer(
    answer: str,
    product: dict | None,
) -> str:
    """
    Финальная защита.

    Артикул существует только внутри системы.
    Клиент не должен его видеть.
    """

    answer = (
        answer or ""
    ).strip()

    if (
        not answer
        or not isinstance(
            product,
            dict,
        )
    ):
        return answer

    article = (
        get_product_article(
            product
        )
    )

    name = str(
        product.get(
            "name",
            "",
        )
        or product.get(
            "title",
            "",
        )
        or ""
    ).strip()

    if (
        article
        and article in answer
    ):

        if name:

            answer = answer.replace(
                article,
                name,
            )

        else:

            answer = answer.replace(
                article,
                "этого товара",
            )

    # Убираем потенциально некрасивые конструкции
    # после замены артикула.

    answer = re.sub(
        r"\bс артикулом\s+этого товара\b",
        "этого товара",
        answer,
        flags=re.IGNORECASE,
    )

    answer = re.sub(
        r"\bартикул(?:ом)?\s*[:\-]?\s*",
        "",
        answer,
        flags=re.IGNORECASE,
    )

    return answer.strip()


# ==========================================================
# PRODUCT MEMORY
# ==========================================================

def should_use_product_memory(
    message: str,
) -> bool:

    normalized = normalize_text(
        message
    )

    words = set(
        re.findall(
            r"[a-zа-яёăâîșşțţ0-9]+",
            normalized,
            flags=re.IGNORECASE,
        )
    )

    if words.intersection(
        PRODUCT_REFERENCE_CUES
    ):

        return True

    if contains_any(
        normalized,
        PRODUCT_QUESTION_CUES,
    ):

        return True

    return False


# ==========================================================
# LOCATION
# ==========================================================

def looks_like_short_location(
    message: str,
) -> bool:

    normalized = normalize_text(
        message
    )

    if not normalized:
        return False

    if "?" in message:
        return False

    words = normalized.split()

    if len(words) > 5:
        return False

    if contains_any(
        normalized,
        PRODUCT_QUESTION_CUES,
    ):
        return False

    return True


# ==========================================================
# LINK ONLY
# ==========================================================

def process_link_only(
    client_id: str,
    instagram_user_id: str,
    message: str,
) -> dict:

    products = load_client_products(
        client_id
    )

    product = find_product_in_message(
        products,
        message,
    )

    add_message(
        client_id=client_id,
        instagram_user_id=instagram_user_id,
        role="user",
        text=message,
    )

    if product is not None:

        set_current_product(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            product=product,
        )

        print(
            f"🔗 [{client_id}] "
            "Товар по ссылке сохранён: "
            f"{product.get('name')}"
        )

    else:

        print(
            f"🔗 [{client_id}] "
            "Получена ссылка, "
            "но товар не найден."
        )

    return {
        "answer": "",
        "route": "link_only",
        "product": product,
        "handoff": False,
    }


# ==========================================================
# DELIVERY
# ==========================================================

def process_delivery_state(
    client_id: str,
    instagram_user_id: str,
    message: str,
    conversation_context: str,
) -> dict | None:

    state = get_state(
        client_id,
        instagram_user_id,
    )

    if (
        state
        != STATE_WAITING_FOR_DELIVERY_CITY
    ):
        return None

    if looks_like_short_location(
        message
    ):

        clear_state(
            client_id,
            instagram_user_id,
        )

        add_message(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            role="user",
            text=message,
        )

        delivery_context = (
            conversation_context
            + "\n\n"
            + "ВАЖНЫЙ КОНТЕКСТ: "
            + "в предыдущем сообщении "
            + "ассистент уточнял город "
            + "или страну доставки. "
            + f"Клиент ответил: {message}. "
            + "Ответь именно про доставку. "
            + "Не переходи к предыдущему "
            + "товару без причины."
        )

        result = route_message(
            client_id=client_id,
            message=(
                "Город или страна доставки: "
                + message
            ),
            current_product=None,
            conversation_context=delivery_context,
        )

        answer = result.get(
            "answer",
            "",
        )

        if answer:

            add_message(
                client_id=client_id,
                instagram_user_id=instagram_user_id,
                role="assistant",
                text=answer,
            )

        return result

    clear_state(
        client_id,
        instagram_user_id,
    )

    return None


# ==========================================================
# MAIN PROCESSING
# ==========================================================

def process_message(
    client_id: str,
    instagram_user_id: str,
    message: str,
    recognized_article: str | None = None,
) -> dict:

    client_id = (
        client_id or ""
    ).strip()

    instagram_user_id = (
        instagram_user_id or ""
    ).strip()

    message = (
        message or ""
    ).strip()

    if not client_id:

        return {
            "answer": (
                "Не удалось определить бизнес."
            ),
            "route": "error",
            "product": None,
            "handoff": False,
        }

    if not instagram_user_id:

        return {
            "answer": (
                "Не удалось определить клиента."
            ),
            "route": "error",
            "product": None,
            "handoff": False,
        }

    # ======================================================
    # VISION PRODUCT HAS ABSOLUTE PRIORITY
    # ======================================================

    recognized_product = None

    if recognized_article:

        recognized_product = (
            find_product_by_article(
                client_id=client_id,
                article=recognized_article,
            )
        )

        if recognized_product:

            start_new_product_context(
                client_id=client_id,
                instagram_user_id=instagram_user_id,
                product=recognized_product,
            )

            print(
                "👁 VISION PRODUCT ACTIVATED: "
                f"{recognized_product.get('name')}"
            )

        else:

            print(
                "⚠️ Vision recognized article "
                f"{recognized_article}, "
                "but product was not found "
                "in products.json"
            )

    # ======================================================
    # EMPTY MESSAGE
    # ======================================================

    if not message:

        if recognized_product:

            message = (
                "Как называется этот товар?"
            )

        else:

            return {
                "answer": "",
                "route": "empty",
                "product": None,
                "handoff": False,
            }

    # ======================================================
    # LINK ONLY
    # ======================================================

    if (
        not recognized_product
        and is_link_only(
            message
        )
    ):

        return process_link_only(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            message=message,
        )

    # ======================================================
    # CONTEXT
    # ======================================================

    conversation_context = (
        get_conversation_context(
            client_id,
            instagram_user_id,
        )
    )

    # ======================================================
    # DELIVERY
    #
    # Если пришла новая фотография,
    # delivery state уже был сброшен.
    # ======================================================

    if not recognized_product:

        delivery_result = (
            process_delivery_state(
                client_id=client_id,
                instagram_user_id=instagram_user_id,
                message=message,
                conversation_context=conversation_context,
            )
        )

        if delivery_result is not None:
            return delivery_result

    # ======================================================
    # SELECT PRODUCT
    # ======================================================

    if recognized_product:

        product_for_router = (
            recognized_product
        )

    else:

        previous_product = (
            get_current_product(
                client_id,
                instagram_user_id,
            )
        )

        if should_use_product_memory(
            message
        ):

            product_for_router = (
                previous_product
            )

        else:

            product_for_router = None

    # ======================================================
    # SAVE USER MESSAGE
    # ======================================================

    add_message(
        client_id=client_id,
        instagram_user_id=instagram_user_id,
        role="user",
        text=message,
    )

    # ======================================================
    # ROUTER
    # ======================================================

    result = route_message(
        client_id=client_id,
        message=message,
        current_product=product_for_router,
        conversation_context=conversation_context,
    )

    answer = result.get(
        "answer",
        "",
    )

    found_product = result.get(
        "product"
    )

    # Если router почему-то не вернул product,
    # но Vision уже определил его,
    # сохраняем recognized_product.

    if (
        not isinstance(
            found_product,
            dict,
        )
        and recognized_product
    ):

        found_product = (
            recognized_product
        )

        result[
            "product"
        ] = recognized_product

    if isinstance(
        found_product,
        dict,
    ):

        set_current_product(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            product=found_product,
        )

    # ======================================================
    # NEVER SHOW ARTICLE TO CUSTOMER
    # ======================================================

    answer = sanitize_answer(
        answer=answer,
        product=(
            found_product
            or recognized_product
            or product_for_router
        ),
    )

    result[
        "answer"
    ] = answer

    # ======================================================
    # DELIVERY STATE
    # ======================================================

    normalized = normalize_text(
        message
    )

    if contains_any(
        normalized,
        DELIVERY_CUES,
    ):

        set_state(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            state=(
                STATE_WAITING_FOR_DELIVERY_CITY
            ),
        )

    # ======================================================
    # SAVE ASSISTANT MESSAGE
    # ======================================================

    if answer:

        add_message(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            role="assistant",
            text=answer,
        )

    # ======================================================
    # DEBUG
    # ======================================================

    print(
        "\n"
        "======================================"
    )

    print(
        f"🏢 CLIENT: {client_id}"
    )

    print(
        f"👤 USER: {instagram_user_id}"
    )

    print(
        f"💬 MESSAGE: {message}"
    )

    if recognized_article:

        print(
            "👁 VISION ARTICLE: "
            f"{recognized_article}"
        )

    print(
        "🧭 ROUTE: "
        f"{result.get('route')}"
    )

    if found_product:

        print(
            "🛍 PRODUCT: "
            f"{found_product.get('name')}"
        )

    print(
        f"🤖 ANSWER: {answer}"
    )

    print(
        "======================================"
        "\n"
    )

    return result


# ==========================================================
# TEXT ONLY WRAPPER
# ==========================================================

def process_message_text(
    client_id: str,
    instagram_user_id: str,
    message: str,
    recognized_article: str | None = None,
) -> str:

    result = process_message(
        client_id=client_id,
        instagram_user_id=instagram_user_id,
        message=message,
        recognized_article=recognized_article,
    )

    return result.get(
        "answer",
        "",
    )