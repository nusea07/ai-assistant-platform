import re

from core.conversation_memory import (
    add_message,
    clear_state,
    get_conversation_context,
    get_current_product,
    get_state,
    set_current_product,
    set_state,
)

from core.message_router import (
    find_product_in_message,
    load_client_products,
    route_message,
)


STATE_WAITING_FOR_DELIVERY_CITY = "waiting_for_delivery_city"


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


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()

    return re.sub(
        r"\s+",
        " ",
        text,
    )


def extract_url(text: str) -> str | None:
    match = re.search(
        r"https?://[^\s]+",
        text or "",
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return None


def get_text_without_url(message: str) -> str:
    url = extract_url(message)

    if not url:
        return message.strip()

    return (
        message
        .replace(url, " ")
        .strip(" \t\r\n-–—")
    )


def is_link_only(message: str) -> bool:
    url = extract_url(message)

    if not url:
        return False

    text_without_url = get_text_without_url(
        message
    )

    return not bool(text_without_url)


def contains_any(
    text: str,
    phrases: set[str],
) -> bool:
    return any(
        phrase in text
        for phrase in phrases
    )


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


def process_message(
    client_id: str,
    instagram_user_id: str,
    message: str,
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
            "answer": "Не удалось определить бизнес.",
            "route": "error",
            "product": None,
            "handoff": False,
        }

    if not instagram_user_id:
        return {
            "answer": "Не удалось определить клиента.",
            "route": "error",
            "product": None,
            "handoff": False,
        }

    if not message:
        return {
            "answer": "",
            "route": "empty",
            "product": None,
            "handoff": False,
        }

    if is_link_only(
        message
    ):

        return process_link_only(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            message=message,
        )

    conversation_context = (
        get_conversation_context(
            client_id,
            instagram_user_id,
        )
    )

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

    previous_product = (
        get_current_product(
            client_id,
            instagram_user_id,
        )
    )

    if should_use_product_memory(
        message
    ):
        product_for_router = previous_product

    else:
        product_for_router = None

    add_message(
        client_id=client_id,
        instagram_user_id=instagram_user_id,
        role="user",
        text=message,
    )

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

    if isinstance(
        found_product,
        dict,
    ):

        set_current_product(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            product=found_product,
        )

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
            state=STATE_WAITING_FOR_DELIVERY_CITY,
        )

    if answer:

        add_message(
            client_id=client_id,
            instagram_user_id=instagram_user_id,
            role="assistant",
            text=answer,
        )

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


def process_message_text(
    client_id: str,
    instagram_user_id: str,
    message: str,
) -> str:

    result = process_message(
        client_id=client_id,
        instagram_user_id=instagram_user_id,
        message=message,
    )

    return result.get(
        "answer",
        "",
    )