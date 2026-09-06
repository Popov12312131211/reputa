from datetime import datetime

from pydantic import BaseModel, Field


class TelegramMessage(BaseModel):
    date: datetime | None = None
    text: str


class ParsedTelegramChannel(BaseModel):
    username: str
    messages: list[TelegramMessage] = Field(default_factory=list)