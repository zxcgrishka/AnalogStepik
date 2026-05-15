from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: str
    test_input: Optional[str] = None
    test_output: str
    course_id: Optional[int] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    test_input: Optional[str] = None
    test_output: str
    course_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True