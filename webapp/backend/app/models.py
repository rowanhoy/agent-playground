from pydantic import BaseModel
from typing import Optional
from pydantic_ai.messages import (
    ModelMessage
)

class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ModelMessage] | None] = None