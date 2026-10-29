"""Instagram Login webhook message handler (pilot).

This file is separate from legacy /webhook/<client_id> integrations.
It never prints message text, access tokens, or database credentials.

Render settings:
  DATABASE_URL, TOKEN_ENCRYPTION_KEY (already configured)
  INSTAGRAM_OAUTH_ALLOWED_USER_ID (already configured)
  INSTAGRAM_OAUTH_AUTO_REPLY_ENABLED=true to enable actual replies
Optional:
  INSTAGRAM_OAUTH_CLIENT_ID=dofamin (only if intentionally testing that client)
  INSTAGRAM_GRAPH_API_VERSION=v26.0
"""

import os
import logging
import requests
import psycopg
from cryptography.fernet import Fernet

LOGGER = logging.getLogger(__name__)


def _token_for_account(account_id: str):
    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=8) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT encrypted_access_token
                   FROM instagram_oauth_accounts
                   WHERE instagram_user_id = %s AND expires_at > NOW()""",
                (account_id,),
            )
            record = cur.fetchone()
    if record is None:
        raise RuntimeError("No unexpired token for target Instagram account")
    key = os.environ["TOKEN_ENCRYPTION_KEY"].strip().encode("ascii")
    return Fernet(key).decrypt(record[0].encode("ascii")).decode("utf-8")


def _reply_text(sender_id: str, user_text: str) -> str:
    client_id = os.getenv("INSTAGRAM_OAUTH_CLIENT_ID", "").strip()
    if not client_id:
        return "Привет! Это тестовое сообщение UNIVERSAL AI ASSISTANT. Подключение Direct работает ✅"
    from core.client_registry import get_client
    from core.assistant_service import process_message_text
    if not get_client(client_id):
        raise RuntimeError("Unknown INSTAGRAM_OAUTH_CLIENT_ID")
    return (process_message_text(
        client_id=client_id,
        instagram_user_id=sender_id,
        message=user_text,
        recognized_article=None,
    ) or "").strip()


def handle_instagram_login_event(payload: dict) -> None:
    """Process signed Instagram webhook data; caller must verify HMAC first."""
    account_id = os.environ.get("INSTAGRAM_OAUTH_ALLOWED_USER_ID", "").strip()
    if not account_id:
        raise RuntimeError("INSTAGRAM_OAUTH_ALLOWED_USER_ID is required")
    enabled = os.getenv("INSTAGRAM_OAUTH_AUTO_REPLY_ENABLED", "false").lower() == "true"
    version = os.getenv("INSTAGRAM_GRAPH_API_VERSION", "v26.0").strip()
    if not version.startswith("v") or not version[1:].replace(".", "").isdigit():
        raise RuntimeError("Invalid INSTAGRAM_GRAPH_API_VERSION")

    for entry in payload.get("entry", []):
        if not isinstance(entry, dict) or str(entry.get("id", "")) != account_id:
            continue
        for event in entry.get("messaging", []):
            if not isinstance(event, dict):
                continue
            sender = str((event.get("sender") or {}).get("id") or "")
            recipient = str((event.get("recipient") or {}).get("id") or "")
            msg = event.get("message") or {}
            if (not isinstance(msg, dict) or not sender or sender == account_id
                    or recipient != account_id or msg.get("is_echo") or msg.get("is_deleted")):
                continue
            user_text = msg.get("text")
            if not isinstance(user_text, str) or not user_text.strip():
                LOGGER.info("Instagram non-text message ignored")
                continue
            LOGGER.info("Instagram incoming text event (content redacted)")
            if not enabled:
                LOGGER.info("Instagram auto-reply is disabled")
                continue
            response_text = _reply_text(sender, user_text)
            if not response_text:
                LOGGER.info("Assistant returned no response")
                continue
            token = _token_for_account(account_id)
            api_response = requests.post(
                f"https://graph.instagram.com/{version}/{account_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={"recipient": {"id": sender}, "message": {"text": response_text[:1000]}},
                timeout=20,
            )
            # Do not log response.body: service messages might contain sensitive details.
            LOGGER.info("Instagram send HTTP status: %s", api_response.status_code)
            if not api_response.ok:
                try:
                    err = api_response.json().get("error", {})
                    LOGGER.error("Instagram send failed: code=%s subcode=%s", err.get("code"), err.get("error_subcode"))
                except ValueError:
                    LOGGER.error("Instagram send failed: non-JSON response")
