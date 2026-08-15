import os
import requests

from core.client_registry import get_client


GRAPH_API_VERSION = "v23.0"


def send_instagram_message(
    client_id: str,
    recipient_id: str,
    message: str,
) -> bool:

    client_config = get_client(client_id)

    if client_config is None:
        print(
            f"Неизвестный client_id: {client_id}"
        )
        return False

    token_env_name = client_config[
        "instagram_access_token_env"
    ]

    account_id_env_name = client_config[
        "instagram_account_id_env"
    ]

    access_token = os.getenv(
        token_env_name
    )

    instagram_account_id = os.getenv(
        account_id_env_name
    )

    if not access_token:
        print(
            f"Отсутствует {token_env_name}"
        )
        return False

    if not instagram_account_id:
        print(
            f"Отсутствует {account_id_env_name}"
        )
        return False

    message = (
        message or ""
    ).strip()

    if not message:
        return True

    url = (
        f"https://graph.instagram.com/"
        f"{GRAPH_API_VERSION}/"
        f"{instagram_account_id}/messages"
    )

    payload = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message
        },
    }

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=20,
        )

        print(
            f"[{client_id}] "
            f"Instagram status: "
            f"{response.status_code}"
        )

        if response.ok:
            print(
                f"[{client_id}] "
                "Сообщение отправлено."
            )
            return True

        print(
            f"[{client_id}] "
            f"Ошибка Instagram API:"
        )

        print(
            response.text
        )

        return False

    except requests.RequestException as error:
        print(
            f"[{client_id}] "
            f"Ошибка запроса Meta: "
            f"{error}"
        )

        return False