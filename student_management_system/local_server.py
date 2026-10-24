#!/usr/bin/env python3
"""
Zero-Dependency Local Development & Testing Server
Runs on Python 3 standard library (no pip installs needed).
Mimics AWS Lambda + API Gateway + DynamoDB behavior locally, and serves the frontend dashboard.
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime, timezone

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DB_FILE = os.path.join(BASE_DIR, 'local_db.json')
SAMPLE_DATA_FILE = os.path.join(BASE_DIR, 'sample_data.json')

def load_db():
    if not os.path.exists(DB_FILE):
        if os.path.exists(SAMPLE_DATA_FILE):
            with open(SAMPLE_DATA_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = []
        save_db(data)
        return data
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class LocalHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self.set_cors_headers()
        self.end_headers()

    def send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def parse_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(body)
        except Exception:
            return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API Routes
        if path == '/api/students' or path == '/students':
            db = load_db()
            department = query.get('department', [None])[0]
            status = query.get('status', [None])[0]
            search = query.get('search', [''])[0].strip().lower()

            results = db
            if department and department != 'All':
                results = [s for s in results if s.get('department') == department]
            if status and status != 'All':
                results = [s for s in results if s.get('status') == status]
            if search:
                results = [
                    s for s in results
                    if search in s.get('first_name', '').lower()
                    or search in s.get('last_name', '').lower()
                    or search in s.get('student_id', '').lower()
                    or search in s.get('email', '').lower()
                ]

            return self.send_json(200, {
                'count': len(results),
                'students': results
            })

        if path.startswith('/api/students/') or (path.startswith('/students/') and not path.endswith('/students')):
            parts = [p for p in path.split('/') if p]
            student_id = parts[-1]
            db = load_db()
            student = next((s for s in db if s.get('student_id') == student_id), None)
            if student:
                return self.send_json(200, {'student': student})
            return self.send_json(404, {'error': f'Student {student_id} not found'})

        if path == '/api/analytics' or path == '/analytics' or path == '/api/stats' or path == '/stats':
            db = load_db()
            total = len(db)
            if total == 0:
                return self.send_json(200, {
                    'total_students': 0,
                    'average_gpa': 0.0,
                    'departments': {},
                    'status_breakdown': {},
                    'year_breakdown': {}
                })

            total_gpa = 0.0
            valid_gpa = 0
            dept_counts = {}
            status_counts = {}
            year_counts = {}

            for s in db:
                try:
                    g = float(s.get('gpa', 0))
                    if g > 0:
                        total_gpa += g
                        valid_gpa += 1
                except Exception:
                    pass

                dept = s.get('department', 'Unknown')
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

                stat = s.get('status', 'Active')
                status_counts[stat] = status_counts.get(stat, 0) + 1

                yr = s.get('year', 'Unknown')
                year_counts[yr] = year_counts.get(yr, 0) + 1

            return self.send_json(200, {
                'total_students': total,
                'average_gpa': round(total_gpa / valid_gpa, 2) if valid_gpa > 0 else 0.0,
                'departments': dept_counts,
                'status_breakdown': status_counts,
                'year_breakdown': year_counts
            })

        # Static files fallback to frontend directory
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()

        if path == '/api/seed' or path == '/seed':
            if os.path.exists(SAMPLE_DATA_FILE):
                with open(SAMPLE_DATA_FILE, 'r') as f:
                    samples = json.load(f)
                save_db(samples)
                return self.send_json(200, {'message': f'Reset and seeded {len(samples)} students', 'seeded_count': len(samples)})
            return self.send_json(400, {'error': 'sample_data.json not found'})

        if path == '/api/students' or path == '/students':
            db = load_db()
            student_id = str(body.get('student_id', '')).strip()
            if not student_id or not body.get('first_name') or not body.get('last_name') or not body.get('email'):
                return self.send_json(400, {'error': 'Missing required fields'})

            if any(s.get('student_id') == student_id for s in db):
                return self.send_json(409, {'error': f'Student {student_id} already exists'})

            now = datetime.now(timezone.utc).isoformat()
            new_student = {
                'student_id': student_id,
                'first_name': str(body.get('first_name', '')).strip(),
                'last_name': str(body.get('last_name', '')).strip(),
                'email': str(body.get('email', '')).strip().lower(),
                'phone': str(body.get('phone', '')).strip(),
                'department': str(body.get('department', 'General')).strip(),
                'year': str(body.get('year', '1st Year')).strip(),
                'gpa': float(body.get('gpa', 0.0)),
                'status': str(body.get('status', 'Active')).strip(),
                'enrollment_date': str(body.get('enrollment_date', now[:10])),
                'courses': body.get('courses', []),
                'created_at': now,
                'updated_at': now
            }
            db.insert(0, new_student)
            save_db(db)
            return self.send_json(201, {'message': 'Student created successfully', 'student': new_student})

        return self.send_json(404, {'error': f'Route not found: POST {path}'})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()

        parts = [p for p in path.split('/') if p]
        if (len(parts) >= 2 and parts[-2] == 'students') or (len(parts) >= 3 and parts[-2] == 'students'):
            student_id = parts[-1]
            db = load_db()
            student = next((s for s in db if s.get('student_id') == student_id), None)
            if not student:
                return self.send_json(404, {'error': f'Student {student_id} not found'})

            for k, v in body.items():
                if k != 'student_id':
                    if k == 'gpa':
                        try:
                            student[k] = float(v)
                        except Exception:
                            pass
                    else:
                        student[k] = v

            student['updated_at'] = datetime.now(timezone.utc).isoformat()
            save_db(db)
            return self.send_json(200, {'message': 'Student updated successfully', 'student': student})

        return self.send_json(404, {'error': f'Route not found: PUT {path}'})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        parts = [p for p in path.split('/') if p]

        if (len(parts) >= 2 and parts[-2] == 'students') or (len(parts) >= 3 and parts[-2] == 'students'):
            student_id = parts[-1]
            db = load_db()
            orig_len = len(db)
            db = [s for s in db if s.get('student_id') != student_id]
            if len(db) == orig_len:
                return self.send_json(404, {'error': f'Student {student_id} not found'})

            save_db(db)
            return self.send_json(200, {'message': f'Student {student_id} deleted successfully'})

        return self.send_json(404, {'error': f'Route not found: DELETE {path}'})

if __name__ == '__main__':
    load_db()
    server_address = ('', PORT)
    httpd = socketserver.TCPServer(server_address, LocalHandler)
    print("=" * 60)
    print(f"🚀 Student Management System Local Server Running!")
    print(f"👉 Open in your browser: http://localhost:{PORT}")
    print(f"👉 API Endpoints: http://localhost:{PORT}/api/students")
    print(f"👉 Press Ctrl+C to stop the server")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped gracefully.")
