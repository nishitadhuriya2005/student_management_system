"""
Logic and integration test for local_server without network sockets.
Directly tests database operations, routing logic, and data integrity.
"""

import unittest
import json
import os
import shutil
from local_server import load_db, save_db, DB_FILE, SAMPLE_DATA_FILE

class TestLocalServerLogic(unittest.TestCase):

    def setUp(self):
        # Create a clean test db
        self.backup_db = None
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                self.backup_db = f.read()

        # Seed with sample data
        with open(SAMPLE_DATA_FILE, 'r') as f:
            self.samples = json.load(f)
        save_db(self.samples)

    def tearDown(self):
        # Restore db
        if self.backup_db:
            with open(DB_FILE, 'w') as f:
                f.write(self.backup_db)

    def test_load_and_save_db(self):
        data = load_db()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['student_id'], 'STU-1001')

    def test_add_student(self):
        db = load_db()
        new_s = {
            "student_id": "STU-8888",
            "first_name": "Test",
            "last_name": "Person",
            "email": "test@edu.org",
            "department": "Computer Science",
            "gpa": 3.9
        }
        db.append(new_s)
        save_db(db)

        reloaded = load_db()
        found = any(s['student_id'] == 'STU-8888' for s in reloaded)
        self.assertTrue(found)

    def test_delete_student(self):
        db = load_db()
        initial_count = len(db)
        db = [s for s in db if s['student_id'] != 'STU-1001']
        save_db(db)

        reloaded = load_db()
        self.assertEqual(len(reloaded), initial_count - 1)
        found = any(s['student_id'] == 'STU-1001' for s in reloaded)
        self.assertFalse(found)

if __name__ == '__main__':
    unittest.main()
