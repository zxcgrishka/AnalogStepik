from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Task, User, TestCase  # Не забудь импортировать TestCase
from app.schemas.task import TaskCreate, TaskResponse
from app.api.deps import get_current_teacher

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    # 1. Формируем объект задачи
    new_task = Task(
        title=task_in.title,
        description=task_in.description,
        course_id = task_in.course_id,
    )

    db.add(new_task)
    await db.flush()

    # 2. Формируем список тестов
    db_test_cases = []
    for test in task_in.test_cases:
        db_tc = TestCase(
            task_id=new_task.id,
            input_data=test.input_data,
            expected_output=test.expected_output,
            is_hidden=test.is_hidden
        )
        db_test_cases.append(db_tc)

    # Массово добавляем все тесты
    db.add_all(db_test_cases)

    # 3. Фиксируем изменения в базе
    await db.commit()

    stmt = select(Task).filter(Task.id == new_task.id).options(selectinload(Task.test_cases))
    result = await db.execute(stmt)
    db_task = result.scalars().first()

    return db_task


@router.get("/", response_model=list[TaskResponse])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    # Используем selectinload для жадной загрузки (Eager Loading) тестов
    stmt = select(Task).options(selectinload(Task.test_cases))
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Task).filter(Task.id == task_id).options(selectinload(Task.test_cases))
    result = await db.execute(stmt)
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task