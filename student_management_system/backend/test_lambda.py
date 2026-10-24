"""
Unit Tests for AWS Lambda Handler
Tests payload parsing, CORS headers, routing, and CRUD logic.
Works in pure Python without needing boto3 installed locally!
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

# If boto3 is not installed locally, mock sys.modules['boto3'] before importing lambda_function
try:
    import boto3
except ImportError:
    mock_boto3 = MagicMock()
    mock_conditions = MagicMock()
    mock_boto3.dynamodb.conditions = mock_conditions
    sys.modules['boto3'] = mock_boto3
    sys.modules['boto3.dynamodb'] = MagicMock()
    sys.modules['boto3.dynamodb.conditions'] = mock_conditions

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lambda_function
import json

class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        self.mock_table = MagicMock()
        lambda_function.table = self.mock_table

    def test_cors_preflight_options(self):
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/students',
            'headers': {}
        }
        response = lambda_function.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')

    def test_get_root_health_check(self):
        event = {
            'requestContext': {'http': {'method': 'GET', 'path': '/'}},
            'queryStringParameters': None
        }
        response = lambda_function.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['status'], 'healthy')

    def test_get_all_students(self):
        self.mock_table.scan.return_value = {
            'Items': [
                {
                    'student_id': 'STU-1001',
                    'first_name': 'Aarav',
                    'last_name': 'Sharma',
                    'department': 'Computer Science',
                    'gpa': 3.88
                }
            ]
        }
        event = {
            'requestContext': {'http': {'method': 'GET', 'path': '/students'}},
            'queryStringParameters': None
        }
        response = lambda_function.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['count'], 1)
        self.assertEqual(body['students'][0]['student_id'], 'STU-1001')

    def test_create_student_validation_error(self):
        # Missing required fields
        event = {
            'requestContext': {'http': {'method': 'POST', 'path': '/students'}},
            'body': json.dumps({'student_id': 'STU-9999'})
        }
        response = lambda_function.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)

    def test_create_student_success(self):
        self.mock_table.get_item.return_value = {}  # No existing student
        event = {
            'requestContext': {'http': {'method': 'POST', 'path': '/students'}},
            'body': json.dumps({
                'student_id': 'STU-2001',
                'first_name': 'Maya',
                'last_name': 'Lin',
                'email': 'maya.lin@university.edu',
                'department': 'Computer Science',
                'gpa': 3.9,
                'status': 'Active'
            })
        }
        response = lambda_function.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 201)
        body = json.loads(response['body'])
        self.assertEqual(body['student']['student_id'], 'STU-2001')

    def test_get_student_by_id(self):
        self.mock_table.get_item.return_value = {
            'Item': {
                'student_id': 'STU-1001',
                'first_name': 'Aarav',
                'last_name': 'Sharma'
            }
        }
        event = {
            'requestContext': {'http': {'method': 'GET', 'path': '/students/STU-1001'}},
            'queryStringParameters': None
        }
        response = lambda_function.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['student']['student_id'], 'STU-1001')

if __name__ == '__main__':
    unittest.main()
