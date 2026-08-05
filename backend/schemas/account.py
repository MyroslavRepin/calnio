from pydantic import BaseModel


class DeleteAccountRequest(BaseModel):
    """Typed-back confirmation, checked on the server rather than in the UI."""

    email: str
