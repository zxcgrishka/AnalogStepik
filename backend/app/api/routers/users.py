from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.db.models import User, Course, Enrollment, Submission
from app.schemas.user import UserProfileResponse, UserStatsResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Профиль текущего пользователя с его курсами"""

    # Получаем курсы пользователя
    result = await db.execute(
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == current_user.id)
    )
    enrolled_courses = result.scalars().all()

    # Добавляем флаг is_enrolled
    for course in enrolled_courses:
        course.is_enrolled = True

    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_teacher": current_user.is_teacher,
        "created_at": current_user.created_at,
        "enrolled_courses": enrolled_courses,
    }


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Статистика пользователя"""

    # Общее количество решений
    total_result = await db.execute(
        select(func.count()).select_from(Submission).where(Submission.user_id == current_user.id)
    )
    total_submissions = total_result.scalar() or 0

    # Количество правильных решений
    correct_result = await db.execute(
        select(func.count()).select_from(Submission).where(
            Submission.user_id == current_user.id,
            Submission.status == "Correct"
        )
    )
    correct_submissions = correct_result.scalar() or 0

    # Количество курсов
    courses_result = await db.execute(
        select(func.count()).select_from(Enrollment).where(Enrollment.user_id == current_user.id)
    )
    courses_enrolled = courses_result.scalar() or 0

    # Точность
    accuracy = (correct_submissions / total_submissions * 100) if total_submissions > 0 else 0

    return {
        "total_submissions": total_submissions,
        "correct_submissions": correct_submissions,
        "accuracy": round(accuracy, 2),
        "courses_enrolled": courses_enrolled,
    }


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """Публичный профиль другого пользователя"""

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return None  # Вернёт 404 автоматически

    # Получаем публичные курсы пользователя (только те, куда он записан)
    result = await db.execute(
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == user_id)
    )
    enrolled_courses = result.scalars().all()

    for course in enrolled_courses:
        course.is_enrolled = True

    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_teacher": user.is_teacher,
        "created_at": user.created_at,
        "enrolled_courses": enrolled_courses,
    }