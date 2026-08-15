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
            Last updated: August 15, 2026
        </p>

        <p>
            This Privacy Policy explains how the AI Assistant Platform
            processes information when interacting with users through
            Instagram messaging.
        </p>

        <h2>Information We Process</h2>

        <p>
            When a user sends a message to an Instagram account connected
            to the AI Assistant Platform, the platform may process
            information provided through that conversation, including
            message content and technical identifiers required to respond
            to the user.
        </p>

        <h2>How Information Is Used</h2>

        <p>
            Information is processed only for purposes such as responding
            to user questions, providing information about products or
            services, maintaining conversation context, and transferring
            requests to a human representative when necessary.
        </p>

        <h2>Third-Party Services</h2>

        <p>
            The platform may use third-party services required for its
            operation, including Meta APIs, hosting providers, and
            artificial intelligence services.
        </p>

        <h2>Data Retention</h2>

        <p>
            Information is retained only as necessary for the operation,
            testing, maintenance, and improvement of the assistant,
            subject to applicable requirements.
        </p>

        <h2>Data Deletion</h2>

        <p>
            Users may request deletion of information associated with
            their interaction with the platform by contacting the
            application operator.
        </p>

        <h2>Contact</h2>

        <p>
            For privacy-related questions or data deletion requests,
            please contact:
        </p>

        <p>
            Email: sochina.nadejda@gmail.com
        </p>

    </body>
    </html>
    """, 200


# ==========================================================
# ENERGY FITNESS PRIVACY POLICY
# ==========================================================

@app.route("/privacy/energy_fitness", methods=["GET"])
def energy_privacy_policy():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ENERGY Fitness - Privacy Policy</title>

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

        <h1>ENERGY Fitness AI Assistant — Privacy Policy</h1>

        <p class="updated">
            Last updated: August 15, 2026
        </p>

        <p>
            This Privacy Policy explains how the ENERGY Fitness AI Assistant
            processes information when users interact with the assistant
            through Instagram messaging.
        </p>

        <h2>Information We Process</h2>

        <p>
            When you contact ENERGY Fitness through Instagram, the assistant
            may process the content of your messages and technical identifiers
            required to receive and respond to the conversation.
        </p>

        <h2>How Information Is Used</h2>

        <p>
            Information may be used to answer questions about ENERGY Fitness,
            provide information about services and training, maintain
            conversation context, and transfer a request to a human
            representative when necessary.
        </p>

        <h2>Third-Party Services</h2>

        <p>
            The assistant may use third-party services necessary for its
            operation, including Meta APIs, hosting infrastructure, and
            artificial intelligence services.
        </p>

        <h2>Data Retention</h2>

        <p>
            Information is retained only when necessary for operation,
            maintenance, testing, security, and improvement of the assistant.
        </p>

        <h2>Data Deletion</h2>

        <p>
            Users may request deletion of information associated with their
            interaction with the ENERGY Fitness AI Assistant.
        </p>

        <p>
            Data deletion instructions are available at:
            /data-deletion/energy_fitness
        </p>

        <h2>Contact</h2>

        <p>
            For privacy questions or data deletion requests, contact:
        </p>

        <p>
            Email: sochina.nadejda@gmail.com
        </p>

    </body>
    </html>
    """, 200


# ==========================================================
# ENERGY FITNESS DATA DELETION
# ==========================================================

@app.route("/data-deletion/energy_fitness", methods=["GET"])
def energy_data_deletion():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ENERGY Fitness - Data Deletion</title>

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
        </style>
    </head>

    <body>

        <h1>ENERGY Fitness AI Assistant — Data Deletion</h1>

        <p>
            You may request deletion of data associated with your interaction
            with the ENERGY Fitness AI Assistant.
        </p>

        <h2>How to request deletion</h2>

        <p>
            Send an email to:
            <strong>sochina.nadejda@gmail.com</strong>
        </p>

        <p>
            Please write “ENERGY Fitness Data Deletion Request”
            in the subject line and provide enough information
            to identify the relevant interaction.
        </p>

        <p>
            After the request is verified, applicable stored information
            associated with the interaction will be deleted.
        </p>

    </body>
    </html>
    """, 200


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
                    and sender_id == business_account_id
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

                message_text = (
                    message_data.get(
                        "text",
                        ""
                    )
                    or ""
                ).strip()

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
                        instagram_user_id=sender_id,
                        message=message_text,
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
                # INSTAGRAM SEND
                # ==========================================

                send_instagram_message(
                    client_id=client_id,
                    recipient_id=sender_id,
                    message=assistant_response,
                )

    except Exception as error:

        print(
            f"[{client_id}] "
            f"Webhook processing error: "
            f"{error}"
        )

    return "EVENT_RECEIVED", 200


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