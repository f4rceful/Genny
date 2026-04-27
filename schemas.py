from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    bt: str
    bp: str
    features: Optional[str] = ""


class GenerateResponse(BaseModel):
    run_id: str
    status: str
    artifacts: list[str]
