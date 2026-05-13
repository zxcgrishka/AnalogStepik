from app.core.celery_app import celery_app
from app.core.runner import run_python_code
from app.db.database import SessionLocal  # Импортируем СИНХРОННУЮ сессию
from app.db.models import Submission, Task

@celery_app.task(name="evaluate_code")
def evaluate_code(submission_id: int, task_id: int, code_text: str):
    """
    Celery задача для запуска кода пользователя в Docker.
    Теперь она полностью синхронная и стабильная.
    """
    # 1. Запускаем тяжелый Docker
    result = run_python_code(code_text)
    actual_output = result.get("output", "").strip()

    # 2. Работаем с БД через обычный context manager
    db = SessionLocal()
    try:
        # Получаем решение и задачу из БД (без await и select!)
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()

        if submission and task:
            # Логика определения статуса остается прежней
            if result.get("status") == "error":
                submission.status = "Runtime Error"
            elif result.get("status") == "timeout":
                submission.status = "Time Limit Exceeded"
            elif actual_output == task.test_output.strip():
                submission.status = "Correct"
            else:
                submission.status = "Wrong Answer"

            submission.output = actual_output
            db.commit() # Синхронный коммит
    except Exception as e:
        db.rollback()
        print(f"Error in worker: {e}")
        raise e
    finally:
        db.close() # Всегда закрываем соединение
