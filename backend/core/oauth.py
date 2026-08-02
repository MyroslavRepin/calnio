from authlib.integrations.starlette_client import OAuth

from backend.core.config import settings

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_oauth_client_id,
    client_secret=settings.google_oauth_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Notion is plain OAuth2, no OIDC discovery, so both endpoints are explicit.
# owner=user is required by Notion and is not part of the OAuth spec. Sending a
# scope param is rejected: capabilities are set on the integration's page.
oauth.register(
    name="notion",
    client_id=settings.notion_oauth_client_id,
    client_secret=settings.notion_oauth_client_secret,
    authorize_url="https://api.notion.com/v1/oauth/authorize",
    access_token_url="https://api.notion.com/v1/oauth/token",
    authorize_params={"owner": "user"},
)

NOTION_REVOKE_URL = "https://api.notion.com/v1/oauth/revoke"
