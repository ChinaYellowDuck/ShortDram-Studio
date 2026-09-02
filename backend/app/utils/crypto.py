"""Cryptography utilities for encrypting sensitive data like API keys."""
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""

    pass


def _get_cipher() -> Fernet:
    """Get the Fernet cipher instance.

    Returns:
        Fernet cipher initialized with the encryption key from settings.

    Raises:
        EncryptionError: If encryption key is not configured.
    """
    if not settings.ENCRYPTION_KEY:
        raise EncryptionError(
            "ENCRYPTION_KEY is not configured. "
            "Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string.

    Args:
        plaintext: The string to encrypt.

    Returns:
        Base64-encoded encrypted string.

    Raises:
        EncryptionError: If encryption fails.
    """
    try:
        cipher = _get_cipher()
        return cipher.encrypt(plaintext.encode()).decode()
    except EncryptionError:
        raise
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}") from e


def decrypt(ciphertext: str) -> str:
    """Decrypt an encrypted string.

    Args:
        ciphertext: The encrypted string to decrypt.

    Returns:
        Decrypted plaintext string.

    Raises:
        EncryptionError: If decryption fails.
    """
    try:
        cipher = _get_cipher()
        return cipher.decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise EncryptionError(
            "Decryption failed: invalid token. The encryption key may have changed."
        ) from e
    except EncryptionError:
        raise
    except Exception as e:
        raise EncryptionError(f"Decryption failed: {e}") from e
