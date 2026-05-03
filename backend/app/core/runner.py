import docker
import tempfile
import os
import shutil
from typing import Dict

try:
    client = docker.from_env()
except Exception as e:
    print(f"Ошибка подключения к Docker: {e}")
    client = None


def run_python_code(code_text: str, timeout: int = 5) -> Dict[str, str]:
    # Запускает код в изолированном Docker-контейнере.
    if client is None:
        return {"status": "error", "output": "Docker Desktop не запущен или не доступен"}

    # Создаем временную папку и файл с кодом
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "solution.py")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code_text)

    try:
        # Запускаем микро-контейнер
        container = client.containers.run(
            image="python:3.11-slim",  # Легкий образ питона
            command="python /code/solution.py",
            # Прокидываем файл в контейнер ТОЛЬКО для чтения (mode: ro)
            volumes={temp_dir: {"bind": "/code", "mode": "ro"}},

            # ПРАВИЛА БЕЗОПАСНОСТИ
            mem_limit="128m",  # Не больше 128 МБ оперативки
            nano_cpus=500000000,  # Не больше 0.5 ядра процессора
            network_disabled=True,  # Отключаем интернет внутри!
            detach=True,  # Запускаем в фоне, чтобы следить за временем
        )

        try:
            # Ждем завершения с учетом таймаута
            result = container.wait(timeout=timeout)
            logs = container.logs().decode("utf-8").strip()

            # Если код упал с ошибкой (например, SyntaxError)
            if result["StatusCode"] != 0:
                return {"status": "fail", "output": logs}

            # Код успешно выполнился
            return {"status": "success", "output": logs}

        except Exception:
            # Если сработал Timeout (бесконечный цикл)
            container.kill()
            return {"status": "timeout", "output": "Time Limit Exceeded (Превышено время выполнения)"}

        finally:
            # Обязательно удаляем контейнер за собой
            container.remove(force=True)

    except Exception as e:
        return {"status": "error", "output": str(e)}

    finally:
        # Удаляем временный файл с кодом
        shutil.rmtree(temp_dir)