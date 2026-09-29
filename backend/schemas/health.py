from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """What the probe answers. Two words, no detail a stranger could use."""

    status: Literal["ok", "down"]
    database: Literal["ok", "down"]
