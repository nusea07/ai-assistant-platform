import os
from pathlib import Path

from flask import Flask, request

from core.assistant_service import process_message_text
from core.instagram_service import send_instagram_message
from core.client_registry import get_client

from core.image_download_service import download_image
from core.product_recognition_service import recognize_product


app = Flask(__name__)


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route("/", methods=["GET"])
def home():
    return "AI Assistant Platform is running", 200


# ==========================================================
# GENERAL PRIVACY POLICY
# ==========================================================

@app.route("/privacy", methods=["GET"])
def privacy_policy():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>Privacy Policy</title>

        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 850px;
                margin: 40px auto;
                padding: 0 20px;
                line-height: 1.6;
                color: #222;
            }

            h1, h2 {
                color: #111;
            }

            .updated {
                color: #666;
                margin-bottom: 30px;
            }
        </style>
    </head>

    <body>

        <h1>Privacy Policy</h1>

        <p class="updated">
            Last updated: August 17, 2026
        </p>

        <p>
            This Privacy Policy explains how the AI Assistant Platform
            processes information when interacting with users through
            Instagram messaging.
        </p>

        <h2>Information We Process</h2>

        <p>
            The platform may process message content, images and
            technical identifiers required to provide responses.
        </p>

        <h2>How Information Is Used</h2>

        <p>
            Information may be used to answer questions about products
            and services, identify products, maintain conversation
            context and transfer conversations to a human representative.
        </p>

        <h2>Third-Party Services</h2>

        <p>
            The platform may use Meta APIs, hosting infrastructure
            and artificial intelligence services.
        </p>

        <h2>Contact</h2>

        <p>
            Email: sochina.nadejda@gmail.com
        </p>

    </body>
    </html>
    """, 200


# ==========================================================
# ENERGY PRIVACY POLICY
# ==========================================================

@app.route("/privacy/energy_fitness", methods=["GET"])
def energy_privacy_policy():

    return """
    <!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>
            ENERGY Fitness - Privacy Policy
        </title>
    </head>

    <body>

        <h1>
            ENERGY Fitness AI Assistant — Privacy Policy
        </h1>

        <p>
            The ENERGY Fitness AI Assistant may process Instagram
            message content and technical identifiers required to
            provide responses.
        </p>

        <p>
            Information is used to answer questions about ENERGY
            Fitness services and to transfer requests to a human
            representative when required.
        </p>

        <p>
            Contact:
            sochina.nadejda@gmail.com
        </p>

    </body>

    </html>
    """, 200


# ==========================================================
# ENERGY DATA DELETION
# ==========================================================

@app.route(
    "/data-deletion/energy_fitness",
    methods=["GET"],
)
def energy_data_deletion():

    return """
    <!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="UTF-8">

        <title>
            ENERGY Fitness - Data Deletion
        </title>
    </head>

    <body>

        <h1>
            ENERGY Fitness AI Assistant — Data Deletion
        </h1>

        <p>
            To request deletion of data associated with your
            interaction with the ENERGY Fitness AI Assistant,
            please contact:
        </p>

        <p>
            <strong>
                sochina.nadejda@gmail.com
            </strong>
        </p>

    </body>

    </html>
    """, 200


# ==========================================================
# EXTRACT IMAGE URL
# ==========================================================

def extract_image_url(message_data: dict):
    """
    Пытается найти изображение в Instagram webhook.

    Поддерживаем:

    1. обычное изображение в Direct
    2. attachment
    3. некоторые Story reply структуры
    """

    # ==========================================
    # NORMAL ATTACHMENTS
    # ==========================================

    attachments = message_data.get(
        "attachments",
        [],
    )

    for attachment in attachments:

        attachment_type = attachment.get(
            "type",
            "",
        )

        payload = attachment.get(
            "payload",
            {},
        ) or {}

        image_url = payload.get(
            "url"
        )

        if (
            attachment_type == "image"
            and image_url
        ):
            return image_url

        # Иногда URL может быть доступен
        # даже если type отличается.

        if image_url:
            return image_url

    # ==========================================
    # STORY REPLY
    # ==========================================

    reply_to = message_data.get(
        "reply_to",
        {},
    ) or {}

    story = reply_to.get(
        "story",
        {},
    ) or {}

    if isinstance(
        story,
        dict,
    ):

        story_url = (
            story.get("url")
            or story.get("media_url")
        )

        if story_url:
            return story_url

    return None


# ==========================================================
# RECOGNIZE DOFAMIN IMAGE
# ==========================================================

def recognize_dofamin_image(
    image_url: str,
):
    """
    Instagram image URL
        ↓
    download
        ↓
    CLIP
        ↓
    TOP-3
        ↓
    Vision
        ↓
    article
    """

    local_image_path = None

    try:

        print(
            "\n======================================"
        )

        print(
            "🖼 DOFAMIN IMAGE RECEIVED"
        )

        print(
            "Downloading image..."
        )

        local_image_path = download_image(
            image_url
        )

        print(
            f"Temporary image: "
            f"{local_image_path}"
        )

        print(
            "Running product recognition..."
        )

        article = recognize_product(
            local_image_path
        )

        if article:

            print(
                f"✅ PRODUCT RECOGNIZED: "
                f"{article}"
            )

        else:

            print(
                "❌ PRODUCT NOT RECOGNIZED"
            )

        print(
            "======================================\n"
        )

        return article

    except Exception as error:

        print(
            "Image recognition error:"
        )

        print(
            error
        )

        return None

    finally:

        if local_image_path:

            try:

                Path(
                    local_image_path
                ).unlink(
                    missing_ok=True
                )

            except Exception:
                pass


# ==========================================================
# WEBHOOK VERIFICATION
# ==========================================================

@app.route(
    "/webhook/<client_id>",
    methods=["GET"],
)
def verify_webhook(client_id: str):

    client_config = get_client(
        client_id
    )

    if client_config is None:

        return (
            "Unknown client",
            404,
        )

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

    return (
        "Forbidden",
        403,
    )


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
            f"Unknown client: "
            f"{client_id}"
        )

        return (
            "EVENT_RECEIVED",
            200,
        )

    data = request.get_json(
        silent=True
    )

    if not data:

        return (
            "EVENT_RECEIVED",
            200,
        )

    print(
        "\n======================================"
    )

    print(
        f"📩 WEBHOOK RECEIVED "
        f"[{client_id}]"
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
            [],
        )

        for entry in entries:

            messaging_events = entry.get(
                "messaging",
                [],
            )

            for event in messaging_events:

                # ==========================================
                # IDS
                # ==========================================

                sender = event.get(
                    "sender",
                    {},
                )

                recipient = event.get(
                    "recipient",
                    {},
                )

                sender_id = str(
                    sender.get(
                        "id",
                        "",
                    )
                ).strip()

                recipient_id = str(
                    recipient.get(
                        "id",
                        "",
                    )
                ).strip()

                if not sender_id:
                    continue

                # ==========================================
                # IGNORE OWN MESSAGES
                # ==========================================

                instagram_account_env = (
                    client_config[
                        "instagram_account_id_env"
                    ]
                )

                business_account_id = os.getenv(
                    instagram_account_env,
                    "",
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

                if message_data.get(
                    "is_echo"
                ):
                    continue

                message_text = str(
                    message_data.get(
                        "text",
                        "",
                    )
                    or ""
                ).strip()

                # ==========================================
                # IMAGE
                # ==========================================

                image_url = extract_image_url(
                    message_data
                )

                recognized_article = None

                # Пока visual recognition
                # включаем ТОЛЬКО для DOFAMIN.

                if (
                    client_id == "dofamin"
                    and image_url
                ):

                    recognized_article = (
                        recognize_dofamin_image(
                            image_url
                        )
                    )

                # ==========================================
                # NO TEXT AND NO PRODUCT
                # ==========================================

                if (
                    not message_text
                    and not recognized_article
                ):

                    print(
                        f"[{client_id}] "
                        "No usable text/product."
                    )

                    continue

                # ==========================================
                # BUILD MESSAGE FOR ASSISTANT
                # ==========================================

                effective_message = (
                    message_text
                )

                if recognized_article:

                    if message_text:

                        effective_message = (
                            f"Клиент говорит о товаре "
                            f"с артикулом "
                            f"{recognized_article}. "
                            f"Вопрос клиента: "
                            f"{message_text}"
                        )

                    else:

                        # Если пользователь отправил
                        # только фотографию.

                        effective_message = (
                            f"Клиент отправил фотографию "
                            f"товара с артикулом "
                            f"{recognized_article}."
                        )

                # ==========================================
                # DEBUG
                # ==========================================

                print(
                    f"\n🏢 BUSINESS: "
                    f"{client_id}"
                )

                print(
                    f"👤 SENDER: "
                    f"{sender_id}"
                )

                print(
                    f"📨 TO: "
                    f"{recipient_id}"
                )

                print(
                    f"💬 ORIGINAL MESSAGE: "
                    f"{message_text}"
                )

                if recognized_article:

                    print(
                        f"🛍 RECOGNIZED ARTICLE: "
                        f"{recognized_article}"
                    )

                print(
                    f"🧠 EFFECTIVE MESSAGE: "
                    f"{effective_message}"
                )

                # ==========================================
                # ASSISTANT
                # ==========================================

                assistant_response = (
                    process_message_text(
                        client_id=client_id,
                        instagram_user_id=sender_id,
                        message=effective_message,
                    )
                )

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
                # SEND TO INSTAGRAM
                # ==========================================

                send_instagram_message(
                    client_id=client_id,
                    recipient_id=sender_id,
                    message=assistant_response,
                )

    except Exception as error:

        print(
            f"[{client_id}] "
            f"Webhook processing error:"
        )

        print(
            error
        )

    return (
        "EVENT_RECEIVED",
        200,
    )


# ==========================================================
# LOCAL / RENDER TEST
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
            "",
        )
    ).strip()

    user_id = str(
        data.get(
            "user_id",
            "local_test_user",
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