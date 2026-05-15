import docker
import tarfile
import io
import requests
from typing import Dict

try:
    client = docker.from_env()
except Exception as e:
    print(f"Ошибка подключения к Docker: {e}")
    client = None


def run_python_code(code_text: str, input_data: str = "", timeout: int = 5) -> Dict[str, str]:
    if client is None:
        return {"status": "error", "output": "Docker Desktop не запущен"}

    container = None
    try:
        # Команда перенаправляет содержимое input.txt в стандартный ввод Python-скрипта
        container = client.containers.create(
            image="python:3.11-slim",
            command='sh -c "python /solution.py < /input.txt"',
            mem_limit="128m",
            nano_cpus=500000000,
            network_disabled=True,
            detach=True
        )

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            # Пакуем файл с кодом
            code_bytes = code_text.encode('utf-8')
            tarinfo_code = tarfile.TarInfo(name='solution.py')
            tarinfo_code.size = len(code_bytes)
            tar.addfile(tarinfo_code, io.BytesIO(code_bytes))

            # Пакуем файл с входными данными (test_input)
            if not input_data.endswith('\n'):
                input_data += '\n'
            input_bytes = input_data.encode('utf-8')
            tarinfo_input = tarfile.TarInfo(name='input.txt')
            tarinfo_input.size = len(input_bytes)
            tar.addfile(tarinfo_input, io.BytesIO(input_bytes))

        tar_stream.seek(0)
        container.put_archive('/', tar_stream)
        container.start()

        # Ждем завершения с учетом таймаута
        try:
            result = container.wait(timeout=timeout)
            status_code = result.get("StatusCode", 0)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            container.kill()
            return {"status": "timeout", "output": "Time Limit Exceeded"}

        logs = container.logs().decode("utf-8").strip()

        if status_code != 0:
            return {"status": "error", "output": logs}

        return {"status": "success", "output": logs}

    except Exception as e:
        if "timeout" in str(e).lower():
            if container: container.kill()
            return {"status": "timeout", "output": "Time Limit Exceeded"}
        return {"status": "error", "output": str(e)}

    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass