from cryptography.fernet import Fernet

from backend.core.config import settings

# The only place Fernet is touched, so there is one module to audit and one
# place to change when key rotation lands. A missing or malformed key raises
# here at import time, so the app refuses to boot rather than failing on the
# first credential write.
fernet = Fernet(settings.credentials_encryption_key.encode())


def encrypt(plaintext: str) -> str:
    """Encrypt a secret for storage, returning a url-safe base64 Fernet token."""
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a stored token, raising InvalidToken if the key changed."""
    return fernet.decrypt(ciphertext.encode()).decode()
