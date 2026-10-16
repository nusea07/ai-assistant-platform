"""Encrypted PostgreSQL storage for Instagram Login tokens.

Required environment variables: DATABASE_URL, TOKEN_ENCRYPTION_KEY.
Never log or return database URLs, encrypted token blobs, or access tokens.
"""
import os
from datetime import datetime, timedelta, timezone

import psycopg
from cryptography.fernet import Fernet


def _cipher():
    key = os.environ.get('TOKEN_ENCRYPTION_KEY', '').strip()
    if not key:
        raise RuntimeError('TOKEN_ENCRYPTION_KEY is missing')
    return Fernet(key.encode('ascii'))


def _connection():
    db_url = os.environ.get('DATABASE_URL', '').strip()
    if not db_url:
        raise RuntimeError('DATABASE_URL is missing')
    return psycopg.connect(db_url, connect_timeout=8)


def save_token(instagram_id: str, token: str, expires_in: int):
    """Upsert an Instagram account's encrypted token in a transaction."""
    if not instagram_id.isdecimal() or not token:
        raise ValueError('Invalid Instagram account ID or token')
    if not 0 < expires_in <= 60 * 60 * 24 * 90:
        raise ValueError('Invalid token expiry')
    ciphertext = _cipher().encrypt(token.encode('utf-8')).decode('ascii')
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS instagram_oauth_accounts (
                    instagram_user_id TEXT PRIMARY KEY,
                    encrypted_access_token TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            ''')
            cur.execute('''
                INSERT INTO instagram_oauth_accounts
                  (instagram_user_id, encrypted_access_token, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (instagram_user_id) DO UPDATE SET
                    encrypted_access_token = EXCLUDED.encrypted_access_token,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
            ''', (instagram_id, ciphertext, expires_at))
    return expires_at
