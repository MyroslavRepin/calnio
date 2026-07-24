from cryptography.fernet import Fernet

from backend.core.config import settings

# The only place Fernet is touched. Everything else calls encrypt/decrypt, so
# there is exactly one module to audit and one place to change when key
# rotation (MultiFernet) lands.
#
# A missing or malformed key raises here, at import time — the app refuses to
# boot rather than failing on the first credential write.
_fernet = Fernet(settings.credentials_encryption_key.encode())


def encrypt(plaintext: str) -> str:
    """Encrypt a secret for storage. Returns a Fernet token (url-safe base64)."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a stored Fernet token back to plaintext.

    Raises cryptography.fernet.InvalidToken if the key changed or the value
    was tampered with.
    """
    return _fernet.decrypt(ciphertext.encode()).decode()
