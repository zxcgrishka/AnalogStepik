import asyncio
from app.core.celery_app import celery_app
from app.core.runner import run_python_code
from app.db.database import AsyncSessionLocal
from app.db.models import Submission, Task
from sqlalchemy import select

async def process_code_async(submission_id: int, task_id: int, code_text: str):
    # Запускаем тяжелый Docker (это синхронная операция, но для воркера это нормально)
    result = run_python_code(code_text)
    actual_output = result.get("output", "").strip()

    async with AsyncSessionLocal() as session:
        # Получаем решение и задачу из БД
        db_sub = await session.execute(select(Submission).where(Submission.id == submission_id))
        db_task = await session.execute(select(Task).where(Task.id == task_id))

        submission = db_sub.scalars().first()
        task = db_task.scalars().first()

        if submission and task:
            if result.get("status") == "error":
                submission.status = "Runtime Error"
            elif result.get("status") == "timeout":
                submission.status = "Time Limit Exceeded"
            elif actual_output == task.test_output.strip():
                submission.status = "Correct"
            else:
                submission.status = "Wrong Answer"

            submission.output = actual_output # Записываем, что именно вывел код студента
            await session.commit()

@celery_app.task(name="evaluate_code")
def evaluate_code(submission_id: int, task_id: int, code_text: str):
    """
    Celery задача для запуска кода пользователя в Docker.
    """
    asyncio.run(process_code_async(submission_id, task_id, code_text))
