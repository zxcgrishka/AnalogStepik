from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SubmissionCreate(BaseModel):
    task_id: int
    code_text: str
    language: str

class SubmissionResponse(BaseModel):
    id: int
    task_id: int
    code_text: str
    language: str
    status: str
    output: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True