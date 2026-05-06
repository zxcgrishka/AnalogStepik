from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Task, User
from app.schemas.task import TaskCreate, TaskResponse

from app.api.deps import get_current_teacher

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    # Формируем объект задачи для БД
    new_task = Task(
        title=task_in.title,
        description=task_in.description,
        test_input=task_in.test_input,
        test_output=task_in.test_output
    )

    # Сохраняем в базу
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task