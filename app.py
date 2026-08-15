import os

from flask import Flask, request

from core.assistant_service import process_message_text
from core.instagram_service import send_instagram_message
from core.client_registry import get_client


app = Flask(__name__)


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route("/", methods=["GET"])
def home():
    return "AI Assistant Platform is running", 200


# ==========================================================
# WEBHOOK VERIFICATION
# ==========================================================

@app.route(
    "/webhook/<client_id>",
    methods=["GET"],
)
def verify_webhook(client_id: str):

    client_config = get_client(client_id)

    if client_config is None:
        return "Unknown client", 404

    verify_token_env = client_config[
        "verify_token_env"
    ]

    expected_token = os.getenv(
        verify_token_env
    )

    mode = request.args.get(
        "hub.mode"
    )

    token = request.args.get(
        "hub.verify_token"
    )

    challenge = request.args.get(
        "hub.challenge"
    )

    print(
        f"[{client_id}] "
        "Webhook verification request"
    )

    if (
        mode == "subscribe"
        and token == expected_token
    ):
        print(
            f"[{client_id}] "
            "Webhook verified successfully"
        )

        return challenge, 200

    print(
        f"[{client_id}] "
        "Webhook verification FAILED"
    )

    return "Forbidden", 403


# ==========================================================
# RECEIVE WEBHOOK
# ==========================================================

@app.route(
    "/webhook/<client_id>",
    methods=["POST"],
)
def receive_webhook(client_id: str):

    client_config = get_client(
        client_id
    )

    if client_config is None:
        print(
            f"Unknown client: {client_id}"
        )

        return "EVENT_RECEIVED", 200

    data = request.get_json(
        silent=True
    )

    if not data:
        return "EVENT_RECEIVED", 200

    print(
        "\n======================================"
    )

    print(
        f"📩 WEBHOOK RECEIVED [{client_id}]"
    )

    print(
        data
    )

    print(
        "======================================"
    )

    try:
        entries = data.get(
            "entry",
            []
        )

        for entry in entries:

            messaging_events = (
                entry.get(
                    "messaging",
                    []
                )
            )

            for event in messaging_events:

                # ==========================================
                # IDS
                # ==========================================

                sender = event.get(
                    "sender",
                    {}
                )

                recipient = event.get(
                    "recipient",
                    {}
                )

                sender_id = str(
                    sender.get(
                        "id",
                        ""
                    )
                ).strip()

                recipient_id = str(
                    recipient.get(
                        "id",
                        ""
                    )
                ).strip()

                if not sender_id:
                    continue

                # ==========================================
                # IGNORE OUR OWN MESSAGES
                # ==========================================

                instagram_account_env = (
                    client_config[
                        "instagram_account_id_env"
                    ]
                )

                business_account_id = (
                    os.getenv(
                        instagram_account_env,
                        ""
                    )
                )

                if (
                    business_account_id
                    and sender_id
                    == business_account_id
                ):
                    print(
                        f"[{client_id}] "
                        "Ignoring own message"
                    )

                    continue

                # ==========================================
                # MESSAGE
                # ==========================================

                message_data = event.get(
                    "message"
                )

                if not message_data:
                    continue

                # Echo = сообщение,
                # отправленное самим бизнесом.
                if message_data.get(
                    "is_echo"
                ):
                    continue

                message_text = (
                    message_data.get(
                        "text",
                        ""
                    )
                    or ""
                ).strip()

                # Пока обрабатываем только текст.
                # Фото подключим через vision_service.py.
                if not message_text:

                    attachments = (
                        message_data.get(
                            "attachments",
                            []
                        )
                    )

                    if attachments:

                        print(
                            f"[{client_id}] "
                            "Получено вложение. "
                            "Vision подключим следующим этапом."
                        )

                    continue

                # ==========================================
                # DEBUG
                # ==========================================

                print(
                    f"\n🏢 BUSINESS: {client_id}"
                )

                print(
                    f"👤 SENDER: {sender_id}"
                )

                print(
                    f"📨 TO: {recipient_id}"
                )

                print(
                    f"💬 MESSAGE: {message_text}"
                )

                # ==========================================
                # ASSISTANT
                # ==========================================

                assistant_response = (
                    process_message_text(
                        client_id=client_id,
                        instagram_user_id=(
                            sender_id
                        ),
                        message=message_text,
                    )
                )

                # Например клиент отправил
                # только ссылку на товар.
                if not assistant_response:

                    print(
                        f"[{client_id}] "
                        "No response required."
                    )

                    continue

                print(
                    f"🤖 RESPONSE: "
                    f"{assistant_response}"
                )

                # ==========================================
                # INSTAGRAM SEND
                # ==========================================

                send_instagram_message(
                    client_id=client_id,
                    recipient_id=sender_id,
                    message=(
                        assistant_response
                    ),
                )

    except Exception as error:

        print(
            f"[{client_id}] "
            f"Webhook processing error: "
            f"{error}"
        )

    # Meta ожидает быстрый 200 OK.
    return "EVENT_RECEIVED", 200


# ==========================================================
# LOCAL TEST
# ==========================================================

@app.route(
    "/test/<client_id>",
    methods=["POST"],
)
def test_assistant(client_id: str):

    client_config = get_client(
        client_id
    )

    if client_config is None:
        return {
            "error": "Unknown client"
        }, 404

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    user_id = str(
        data.get(
            "user_id",
            "local_test_user"
        )
    ).strip()

    if not message:
        return {
            "error": (
                "Field 'message' "
                "is required"
            )
        }, 400

    answer = process_message_text(
        client_id=client_id,
        instagram_user_id=user_id,
        message=message,
    )

    return {
        "client_id": client_id,
        "user_id": user_id,
        "message": message,
        "answer": answer,
    }, 200


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
    )