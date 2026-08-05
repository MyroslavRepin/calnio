from pydantic import BaseModel, ConfigDict


class MeResponse(BaseModel):
    """The signed-in user's profile, as the dashboard sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None
    picture: str | None
