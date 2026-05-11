import docker
import tarfile
import io
import time
import requests
from typing import Dict

try:
    client = docker.from_env()
except Exception as e:
    print(f"Ошибка подключения к Docker: {e}")
    client = None

def run_python_code(code_text: str, timeout: int = 5) -> Dict[str, str]:
    if client is None:
        return {"status": "error", "output": "Docker Desktop не запущен или не доступен"}

    container = None
    try:
        # Создаем контейнер без запуска
        container = client.containers.create(
            image="python:3.11-slim",
            command="python /solution.py",
            mem_limit="128m",
            nano_cpus=500000000,
            network_disabled=True,
            detach=True
        )

        # Создаем архив в памяти с файлом solution.py
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            code_bytes = code_text.encode('utf-8')
            tarinfo = tarfile.TarInfo(name='solution.py')
            tarinfo.size = len(code_bytes)
            tar.addfile(tarinfo, io.BytesIO(code_bytes))
        
        tar_stream.seek(0)
        # Копируем архив в контейнер в корневую директорию
        container.put_archive('/', tar_stream)

        # Запускаем контейнер
        container.start()

        # Ждем завершения с учетом таймаута
        result = container.wait(timeout=timeout)
        logs = container.logs().decode("utf-8").strip()

        if result["StatusCode"] != 0:
            return {"status": "fail", "output": logs}

        return {"status": "success", "output": logs}

    except requests.exceptions.ReadTimeout:
        if container:
            container.kill()
        return {"status": "timeout", "output": "Time Limit Exceeded (Превышено время выполнения)"}
    except Exception as e:
        # Пытаемся поймать другие виды таймаутов, если docker-py кидает их
        if "Timeout" in str(e):
            if container:
                container.kill()
            return {"status": "timeout", "output": "Time Limit Exceeded (Превышено время выполнения)"}
        return {"status": "error", "output": str(e)}

    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass