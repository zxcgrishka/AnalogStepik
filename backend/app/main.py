from fastapi import FastAPI
from app.api.routers import auth, submissions, tasks, courses, users
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json"
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(submissions.router)
app.include_router(tasks.router)
app.include_router(courses.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "print('Hello World!')"}
