import time
import requests

BASE_URL = "http://localhost:8000"

def run_tests():
    print("Starting E2E Tests...")
    
    # 1. Register a user
    user_email = f"testuser_{int(time.time())}@example.com"
    password = "securepassword123"
    print(f"Registering user: {user_email}")
    res = requests.post(f"{BASE_URL}/auth/register", json={"email": user_email, "password": password})
    assert res.status_code == 200, f"Failed to register: {res.text}"
    user_id = res.json()["id"]
    
    # 2. Login
    print("Logging in...")
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": user_email, "password": password})
    assert res.status_code == 200, f"Failed to login: {res.text}"
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create a task (Oops, the endpoint requires is_teacher=True)
    # We will temporarily bypass this by manually updating the user in DB to be a teacher
    # Since we can't easily do it from here without psycopg2, let's just make a POST request
    # If it fails with 403, we know it works.
    print("Attempting to create a task as a normal user...")
    res = requests.post(f"{BASE_URL}/tasks/", json={
        "title": "Sum",
        "description": "Print sum of 2 and 2",
        "test_input": "",
        "test_output": "4"
    }, headers=headers)
    assert res.status_code in [403, 200], f"Unexpected status: {res.status_code}"
    
    if res.status_code == 403:
        print("User is not a teacher. Setting up via raw DB execution...")
        import subprocess
        # Make the user a teacher
        subprocess.run(["docker", "compose", "exec", "-T", "db", "psql", "-U", "user", "-d", "stepik_db", "-c", f"UPDATE users SET is_teacher=true WHERE id={user_id};"], check=True)
        
        # Try again
        res = requests.post(f"{BASE_URL}/tasks/", json={
            "title": "Sum",
            "description": "Print sum of 2 and 2",
            "test_input": "",
            "test_output": "4"
        }, headers=headers)
        assert res.status_code == 200, f"Failed to create task: {res.text}"
        
    task_id = res.json()["id"]
    print(f"Task created with ID: {task_id}")
    
    # 4. Submit correct code
    print("Submitting code...")
    code_text = "print(4)"
    res = requests.post(f"{BASE_URL}/submissions/", json={
        "task_id": task_id,
        "code_text": code_text,
        "language": "python"
    }, headers=headers)
    assert res.status_code == 200, f"Failed to submit code: {res.text}"
    sub_id = res.json()["id"]
    print(f"Submission created with ID: {sub_id}")
    
    # 5. Poll for result
    print("Waiting for Celery worker to process...")
    for _ in range(10):
        time.sleep(2)
        res = requests.get(f"{BASE_URL}/submissions/{sub_id}", headers=headers)
        assert res.status_code == 200, f"Failed to fetch submission: {res.text}"
        status = res.json()["status"]
        print(f"Current status: {status}")
        if status != "pending":
            assert status == "Correct", f"Expected 'Correct', got {status}"
            print("SUCCESS! Tests passed.")
            return
            
    print("FAILED: Worker did not process the submission in time.")
    exit(1)

if __name__ == "__main__":
    run_tests()
