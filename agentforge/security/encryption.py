"""
AgentForge Security – AES-256 Encryption.

Fernet symmetric encryption for API keys stored in the database.
Generates and manages encryption keys securely.
"""

from __future__ import annotations

import base64
import os
from functools import lru_cache
from typing import Optional

from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)

try:
    from cryptography.fernet import Fernet, InvalidToken
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    logger.warning("cryptography package not installed. Encryption disabled.")


@lru_cache(maxsize=1)
def _get_fernet() -> Optional[object]:
    """Return a Fernet cipher instance, creating a key if needed."""
    if not _CRYPTO_AVAILABLE:
        return None

    from agentforge.config import get_config
    cfg = get_config()

    key = cfg.auth.encryption_key
    if not key:
        # Auto-generate a key and log it (user should persist it)
        key = Fernet.generate_key().decode()
        logger.warning(
            f"No AUTH_ENCRYPTION_KEY set. Generated ephemeral key (not persisted): {key[:16]}..."
        )
        logger.warning("Set AUTH_ENCRYPTION_KEY in .env for production use!")

    # Ensure the key is valid Fernet format
    try:
        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = key
        return Fernet(key_bytes)
    except Exception:
        # Try to pad/fix the key
        try:
            padded = base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b'\x00'))
            return Fernet(padded)
        except Exception as e:
            logger.error(f"Invalid encryption key: {e}")
            return None


def encrypt(plaintext: str) -> str:
    """
    Encrypt a plaintext string using AES-256 (Fernet).

    Args:
        plaintext: The string to encrypt

    Returns:
        Base64-encoded encrypted string, or plaintext if encryption unavailable
    """
    fernet = _get_fernet()
    if not fernet:
        return plaintext  # Fallback: no encryption

    try:
        token = fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return plaintext


def decrypt(ciphertext: str) -> str:
    """
    Decrypt a Fernet-encrypted string.

    Args:
        ciphertext: The encrypted string to decrypt

    Returns:
        Decrypted plaintext string, or ciphertext if decryption fails
    """
    fernet = _get_fernet()
    if not fernet:
        return ciphertext

    try:
        plaintext = fernet.decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")
    except Exception:
        # Return as-is if decryption fails (may be unencrypted value)
        return ciphertext


def generate_new_key() -> str:
    """Generate a new Fernet encryption key."""
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography package not installed")
    return Fernet.generate_key().decode()


def is_encrypted(value: str) -> bool:
    """Heuristic check if a value appears to be Fernet-encrypted."""
    if not value or len(value) < 50:
        return False
    try:
        decoded = base64.urlsafe_b64decode(value + "==")
        return decoded[0:1] == b"\x80"  # Fernet token magic byte
    except Exception:
        return False
