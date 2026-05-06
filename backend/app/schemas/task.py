from pydantic import BaseModel
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    description: str
    test_input: Optional[str] = None
    test_output: str

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    test_input: Optional[str] = None
    test_output: str

    class Config:
        from_attributes = True