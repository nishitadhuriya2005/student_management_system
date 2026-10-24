"""
End-to-End local integration test.
Tests the REST API and data storage by simulating HTTP client requests.
"""

import threading
import time
import urllib.request
import json
import socketserver
from local_server import LocalHandler, PORT

def run_tests():
    base_url = f"http://127.0.0.1:{PORT}"
    print(f"Connecting to test server at {base_url}...")

    # 1. Health check / GET /students
    req = urllib.request.Request(f"{base_url}/students")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        assert 'students' in data, "Key 'students' missing in response"
        print(f"✅ GET /students passed! ({len(data['students'])} students found)")

    # 2. POST /students (Create student)
    new_student = {
        "student_id": "STU-9999",
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@university.edu",
        "phone": "+1-555-9999",
        "department": "Computer Science",
        "year": "2nd Year",
        "gpa": 3.95,
        "status": "Active",
        "enrollment_date": "2024-01-01",
        "courses": ["Cloud Systems"]
    }
    req = urllib.request.Request(
        f"{base_url}/students",
        data=json.dumps(new_student).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        assert resp.status == 201, f"Expected 201, got {resp.status}"
        assert data['student']['student_id'] == 'STU-9999'
        print("✅ POST /students passed!")

    # 3. GET /students/STU-9999
    req = urllib.request.Request(f"{base_url}/students/STU-9999")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        assert resp.status == 200
        assert data['student']['first_name'] == 'Test'
        print("✅ GET /students/STU-9999 passed!")

    # 4. PUT /students/STU-9999
    update_data = {"first_name": "UpdatedTest", "gpa": 4.00}
    req = urllib.request.Request(
        f"{base_url}/students/STU-9999",
        data=json.dumps(update_data).encode(),
        headers={'Content-Type': 'application/json'},
        method='PUT'
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        assert resp.status == 200
        assert data['student']['first_name'] == 'UpdatedTest'
        assert data['student']['gpa'] == 4.00
        print("✅ PUT /students/STU-9999 passed!")

    # 5. GET /analytics
    req = urllib.request.Request(f"{base_url}/analytics")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        assert resp.status == 200
        assert 'departments' in data
        assert 'total_students' in data
        print(f"✅ GET /analytics passed! (Avg GPA: {data['average_gpa']})")

    # 6. DELETE /students/STU-9999
    req = urllib.request.Request(f"{base_url}/students/STU-9999", method='DELETE')
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        assert resp.status == 200
        print("✅ DELETE /students/STU-9999 passed!")

    print("\n🎉 ALL END-TO-END TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    # Start server in background thread
    server = socketserver.TCPServer(('127.0.0.1', PORT), LocalHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.5)

    try:
        run_tests()
    finally:
        server.shutdown()
        server.server_close()
