from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.oauth_account import OAuthAccount
from backend.models.user import User


class UserRepo:
    """User persistence. Caller owns the session and the commit."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_oauth(self, provider: str, provider_account_id: str) -> User | None:
        account = self.db.scalar(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_account_id == provider_account_id,
            )
        )
        return account.user if account else None

    def get_or_create_user_oauth(
        self,
        provider: str,
        provider_account_id: str,
        *,
        email: str,
        name: str | None = None,
        picture: str | None = None,
    ) -> User:
        user = self.get_by_oauth(provider, provider_account_id)
        if user:
            # Profile may have changed on the provider side since last login.
            user.name = name
            user.picture = picture
            return user

        user = self.get_by_email(email)
        if user is None:
            user = User(email=email, name=name, picture=picture)
            self.db.add(user)

        user.oauth_accounts.append(
            OAuthAccount(provider=provider, provider_account_id=provider_account_id)
        )
        self.db.flush()  # assign ids so caller can mint tokens before commit
        return user
