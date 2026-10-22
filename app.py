import os
from pathlib import Path
import secrets
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import hmac
import hashlib

from flask import Flask, request, redirect, session

from core.assistant_service import (
    process_message_text,
)

from core.instagram_service import (
    send_instagram_message,
)

from core.client_registry import (
    get_client,
)

from core.image_download_service import (
    download_image,
)

from core.product_recognition_service import (
    recognize_product,
)


app = Flask(__name__)
app.secret_key = os.getenv("OAUTH_SESSION_SECRET")
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route(
    "/",
    methods=["GET"],
)
def home():

    return (
        "AI Assistant Platform is running",
        200,
    )


# ==========================================================
# GENERAL PRIVACY POLICY
# ==========================================================

@app.route(
    "/privacy",
    methods=["GET"],
)
def privacy_policy():

    return """
    <!DOCTYPE html>
    <html lang="en">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>
            Privacy Policy
        </title>

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

        <h1>
            Privacy Policy
        </h1>

        <p class="updated">
            Last updated: August 17, 2026
        </p>

        <p>
            This Privacy Policy explains how the
            AI Assistant Platform processes information
            when interacting with users through
            Instagram messaging.
        </p>

        <h2>
            Information We Process
        </h2>

        <p>
            The platform may process message content,
            images and technical identifiers required
            to provide responses.
        </p>

        <h2>
            How Information Is Used
        </h2>

        <p>
            Information may be used to answer questions
            about products and services, identify
            products, maintain conversation context
            and transfer conversations to a human
            representative.
        </p>

        <h2>
            Third-Party Services
        </h2>

        <p>
            The platform may use Meta APIs,
            hosting infrastructure and artificial
            intelligence services.
        </p>

        <h2>
            Contact
        </h2>

        <p>
            Email: sochina.nadejda@gmail.com
        </p>

    </body>

    </html>
    """, 200


# ==========================================================
# GENERAL DATA DELETION INSTRUCTIONS
# ==========================================================

@app.route("/data-deletion", methods=["GET"])
def data_deletion_instructions():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Data Deletion Instructions | UNIVERSAL AI ASSISTANT</title>
        <style>
            body {font-family: Arial, sans-serif; max-width: 850px;
                  margin: 40px auto; padding: 0 20px; line-height: 1.65;
                  color: #222;}
            h1, h2 {color: #111;}
            a {color: #1558b0;}
        </style>
    </head>
    <body>
        <h1>Data Deletion Instructions</h1>
        <p>These instructions apply to UNIVERSAL AI ASSISTANT
           (AI Assistant Platform), which supports Instagram messaging
           for participating businesses.</p>
        <h2>How to request deletion</h2>
        <p>To request deletion of personal data associated with your
           interactions with the AI assistant, send an email to
           <a href="mailto:sochina.nadejda@gmail.com">sochina.nadejda@gmail.com</a>
           with the subject <strong>Data Deletion Request</strong>.</p>
        <p>Please include the Instagram username used in the interaction
           and, if known, the business account you contacted. Do not
           include your password, access tokens, or other sensitive login
           information.</p>
        <h2>What happens next</h2>
        <p>We will use the details you provide to identify applicable
           information, verify the request when necessary, and respond
           with the available deletion steps. Some information may need
           to be retained where required by law or for legitimate
           security purposes.</p>
        <p>Removing app access in Instagram or Meta settings revokes
           future access but does not by itself guarantee deletion of
           information already processed. Please email us to request
           deletion of previously processed data.</p>
        <h2>Contact</h2>
        <p><a href="mailto:sochina.nadejda@gmail.com">sochina.nadejda@gmail.com</a></p>
    </body>
    </html>
    """, 200, {"Content-Type": "text/html; charset=utf-8"}


# ==========================================================
# ENERGY PRIVACY POLICY
# ==========================================================

@app.route(
    "/privacy/energy_fitness",
    methods=["GET"],
)
def energy_privacy_policy():

    return """
    <!DOCTYPE html>
    <html lang="en">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>
            ENERGY Fitness - Privacy Policy
        </title>

    </head>

    <body>

        <h1>
            ENERGY Fitness AI Assistant —
            Privacy Policy
        </h1>

        <p>
            The ENERGY Fitness AI Assistant may process
            Instagram message content and technical
            identifiers required to provide responses.
        </p>

        <p>
            Information is used to answer questions
            about ENERGY Fitness services and to
            transfer requests to a human representative
            when required.
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
            ENERGY Fitness AI Assistant —
            Data Deletion
        </h1>

        <p>
            To request deletion of data associated
            with your interaction with the ENERGY
            Fitness AI Assistant, please contact:
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

def extract_image_url(
    message_data: dict,
):

    # ==========================================
    # DIRECT ATTACHMENTS
    # ==========================================

    attachments = (
        message_data.get(
            "attachments",
            [],
        )
        or []
    )

    for attachment in attachments:

        payload = (
            attachment.get(
                "payload",
                {},
            )
            or {}
        )

        image_url = payload.get(
            "url"
        )

        if image_url:
            return image_url

    # ==========================================
    # STORY REPLY
    # ==========================================

    reply_to = (
        message_data.get(
            "reply_to",
            {},
        )
        or {}
    )

    story = (
        reply_to.get(
            "story",
            {},
        )
        or {}
    )

    if isinstance(
        story,
        dict,
    ):

        story_url = (
            story.get(
                "url"
            )
            or story.get(
                "media_url"
            )
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

        local_image_path = (
            download_image(
                image_url
            )
        )

        print(
            "Running product recognition..."
        )

        article = recognize_product(
            local_image_path
        )

        if article:

            print(
                "✅ PRODUCT RECOGNIZED: "
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
def verify_webhook(
    client_id: str,
):

    client_config = get_client(
        client_id
    )

    if client_config is None:

        return (
            "Unknown client",
            404,
        )

    verify_token_env = (
        client_config[
            "verify_token_env"
        ]
    )

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
def receive_webhook(
    client_id: str,
):

    client_config = get_client(
        client_id
    )

    if client_config is None:

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

            messaging_events = (
                entry.get(
                    "messaging",
                    [],
                )
            )

            for event in messaging_events:

                # ======================================
                # IDS
                # ======================================

                sender_id = str(
                    event.get(
                        "sender",
                        {},
                    ).get(
                        "id",
                        "",
                    )
                ).strip()

                recipient_id = str(
                    event.get(
                        "recipient",
                        {},
                    ).get(
                        "id",
                        "",
                    )
                ).strip()

                if not sender_id:
                    continue

                # ======================================
                # IGNORE OWN MESSAGES
                # ======================================

                instagram_account_env = (
                    client_config[
                        "instagram_account_id_env"
                    ]
                )

                business_account_id = (
                    os.getenv(
                        instagram_account_env,
                        "",
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

                # ======================================
                # MESSAGE
                # ======================================

                message_data = (
                    event.get(
                        "message"
                    )
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

                # ======================================
                # IMAGE
                # ======================================

                image_url = (
                    extract_image_url(
                        message_data
                    )
                )

                recognized_article = None

                if (
                    client_id == "dofamin"
                    and image_url
                ):

                    recognized_article = (
                        recognize_dofamin_image(
                            image_url
                        )
                    )

                # ======================================
                # NOTHING TO PROCESS
                # ======================================

                if (
                    not message_text
                    and not recognized_article
                ):

                    continue

                # ======================================
                # DEBUG
                # ======================================

                print(
                    f"\n🏢 BUSINESS: "
                    f"{client_id}"
                )

                print(
                    f"👤 SENDER: "
                    f"{sender_id}"
                )

                print(
                    f"💬 MESSAGE: "
                    f"{message_text}"
                )

                if recognized_article:

                    print(
                        "👁 INTERNAL ARTICLE: "
                        f"{recognized_article}"
                    )

                # ======================================
                # ASSISTANT
                #
                # Article передаётся ОТДЕЛЬНО.
                # Клиент его не видит.
                # ======================================

                assistant_response = (
                    process_message_text(
                        client_id=client_id,
                        instagram_user_id=sender_id,
                        message=message_text,
                        recognized_article=(
                            recognized_article
                        ),
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

                # ======================================
                # SEND
                # ======================================

                send_instagram_message(
                    client_id=client_id,
                    recipient_id=sender_id,
                    message=assistant_response,
                )

    except Exception as error:

        print(
            f"[{client_id}] "
            "Webhook processing error:"
        )

        print(
            error
        )

    return (
        "EVENT_RECEIVED",
        200,
    )


# ==========================================================
# TEST ENDPOINT
# ==========================================================

@app.route(
    "/test/<client_id>",
    methods=["POST"],
)
def test_assistant(
    client_id: str,
):

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

    recognized_article = (
        data.get(
            "recognized_article"
        )
    )

    if recognized_article is not None:

        recognized_article = str(
            recognized_article
        ).strip()

    if (
        not message
        and not recognized_article
    ):

        return {
            "error": (
                "Field 'message' or "
                "'recognized_article' "
                "is required"
            )
        }, 400

    answer = process_message_text(
        client_id=client_id,
        instagram_user_id=user_id,
        message=message,
        recognized_article=(
            recognized_article
        ),
    )

    return {
        "client_id": client_id,
        "user_id": user_id,
        "message": message,
        "recognized_article": (
            recognized_article
        ),
        "answer": answer,
    }, 200


# ==========================================================
# INSTAGRAM LOGIN OAUTH TEST (INDEPENDENT OF EXISTING WEBHOOKS)
# ==========================================================
# Set these on Render > Environment (do not put secrets in GitHub):
# INSTAGRAM_APP_ID = Instagram App ID (NOT Meta/Facebook App ID)
# INSTAGRAM_APP_SECRET = Instagram App Secret
# OAUTH_SESSION_SECRET = long random secret for signing test session
# INSTAGRAM_OAUTH_REDIRECT_URI = exact approved Instagram Login redirect URL
# Example:
# https://ai-assistant-platform-mq4h.onrender.com/instagram/oauth/callback
#
# After Instagram Login this saves a *long-lived* token encrypted in Postgres.
# It does not print tokens or connect Direct messages automatically.
# Restrict use to INSTAGRAM_OAUTH_ALLOWED_USER_ID during testing.

_OAUTH_SCOPES = (
    "instagram_business_basic,instagram_business_manage_messages"
)


def _oauth_settings():
    return (
        os.getenv("INSTAGRAM_APP_ID", "").strip(),
        os.getenv("INSTAGRAM_APP_SECRET", "").strip(),
        os.getenv("INSTAGRAM_OAUTH_REDIRECT_URI", "").strip(),
        os.getenv("OAUTH_SESSION_SECRET", "").strip(),
    )


@app.route("/instagram/oauth/start", methods=["GET"])
def instagram_oauth_start():
    client_id, client_secret, callback, cookie_secret = _oauth_settings()
    if not all((client_id, client_secret, callback, cookie_secret)):
        return "Instagram OAuth test is not configured on this server.", 503
    if not callback.startswith("https://"):
        return "Redirect URI must be HTTPS.", 503
    # Flask signs this browser cookie; use a stable secret across deployments.
    state = secrets.token_urlsafe(32)
    session["instagram_oauth_state"] = state
    params = urlencode({
        "client_id": client_id,
        "redirect_uri": callback,
        "response_type": "code",
        "scope": _OAUTH_SCOPES,
        "state": state,
    })
    return redirect("https://www.instagram.com/oauth/authorize?" + params)


@app.route("/instagram/oauth/callback", methods=["GET"])
def instagram_oauth_callback():
    client_id, client_secret, callback, cookie_secret = _oauth_settings()
    if not all((client_id, client_secret, callback, cookie_secret)):
        return "Instagram OAuth test is not configured on this server.", 503
    state = request.args.get("state", "")
    expected_state = session.pop("instagram_oauth_state", None)
    if not expected_state or not secrets.compare_digest(state, expected_state):
        return "OAuth state mismatch. Restart from /instagram/oauth/start.", 400
    if request.args.get("error"):
        return "Instagram did not grant access. Check consent and account role.", 400
    code = request.args.get("code", "")
    if not code:
        return "No authorization code received from Instagram.", 400
    # Meta can append '#_' to codes; fragments are removed from HTTP URLs.
    # Some integrations report a code suffixed with '#_' in other contexts.
    code = code.removesuffix("#_")
    body = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "redirect_uri": callback,
        "code": code,
    }).encode("utf-8")
    req = Request(
        "https://api.instagram.com/oauth/access_token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError):
        # Never echo Meta's full error: it can contain request details.
        return (
            "Instagram authorization code exchange failed. "
            "Check that Redirect URI is saved in Meta and matches exactly, "
            "and that this code was not used before.",
            502,
        )
    if not result.get("access_token"):
        return "Instagram returned no access token.", 502
    ig_id = str(result.get("user_id", ""))
    allowed_id = os.getenv("INSTAGRAM_OAUTH_ALLOWED_USER_ID", "").strip()
    # During development, reject all accounts except the explicit test user.
    if not allowed_id or not secrets.compare_digest(ig_id, allowed_id):
        return "Instagram account is not approved for this test.", 403

    short_token = result["access_token"]
    # Exchange the one-hour token for a longer-lived token before storage.
    exchange_query = urlencode({
        "grant_type": "ig_exchange_token",
        "client_secret": client_secret,
        "access_token": short_token,
    })
    exchange_request = Request(
        "https://graph.instagram.com/access_token?" + exchange_query,
        method="GET",
    )
    try:
        with urlopen(exchange_request, timeout=20) as response:
            long_result = json.loads(response.read().decode("utf-8"))
        long_token = long_result["access_token"]
        expires_in = int(long_result["expires_in"])
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError):
        # Never store a short-lived token as though it were a 60-day token.
        return "Instagram authorized, but long-lived token exchange failed.", 502

    try:
        from oauth_token_store import save_token
        expiry = save_token(ig_id, long_token, expires_in)
    except Exception:
        # In particular never dump DB exception details or credentials.
        return "Instagram authorized, but secure database storage failed.", 503

    return (
        "Instagram connected successfully. "
        "Instagram user ID: " + ig_id + ". "
        "Encrypted token saved. "
        "Expires (UTC): " + expiry.strftime("%Y-%m-%d %H:%M") + ". "
        "Direct messages are not connected yet.",
        200,
    )


# ==========================================================
# INSTAGRAM LOGIN WEBHOOK (separate from legacy client webhooks)
# ==========================================================

@app.route("/instagram/webhook", methods=["GET"])
def instagram_login_webhook_verify():
    expected = os.getenv("INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "").strip()
    provided = request.args.get("hub.verify_token", "")
    challenge = request.args.get("hub.challenge", "")
    mode = request.args.get("hub.mode", "")
    if (expected and mode == "subscribe" and challenge
            and hmac.compare_digest(provided, expected)):
        return challenge, 200, {"Content-Type": "text/plain; charset=utf-8"}
    return "Forbidden", 403


@app.route("/instagram/webhook", methods=["POST"])
def instagram_login_webhook_receive():
    # The secret must be the Instagram App Secret matching the configured app.
    app_secret = os.getenv("INSTAGRAM_APP_SECRET", "").strip()
    if not app_secret:
        return "Webhook not configured", 503
    signature = request.headers.get("X-Hub-Signature-256", "")
    raw_payload = request.get_data(cache=True)
    expected_signature = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), raw_payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return "Invalid signature", 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return "Invalid payload", 400
    if data.get("object") != "instagram":
        return "Unsupported object", 400
    # Test mode: acknowledge signed events only. No message text, sender IDs,
    # or raw payloads are logged, and no automatic replies are sent yet.
    return "EVENT_RECEIVED", 200


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
