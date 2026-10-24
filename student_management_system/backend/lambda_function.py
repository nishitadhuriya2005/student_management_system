"""
AWS Lambda Function for Student Management System
Serverless Backend using AWS Lambda and Amazon DynamoDB
Configured for 100% AWS Free Tier compliance
"""

import json
import os
import decimal
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key, Attr

# Helper class to convert DynamoDB Decimal types to float/int for JSON serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Helper to convert float to Decimal before writing to DynamoDB
def float_to_decimal(obj):
    if isinstance(obj, float):
        return decimal.Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [float_to_decimal(v) for v in obj]
    return obj

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'StudentManagementTable')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# Standard HTTP response headers with CORS enabled
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
}

def build_response(status_code, body):
    """Formats standard HTTP response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def parse_body(event):
    """Safely extracts JSON body from API Gateway event."""
    body = event.get('body')
    if not body:
        return {}
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except Exception:
        return {}

def extract_path_and_method(event):
    """Normalizes path and method across API Gateway payload v1 and v2 formats."""
    # API Gateway HTTP API (Payload v2)
    http_context = event.get('requestContext', {}).get('http', {})
    method = http_context.get('method')
    path = http_context.get('path')

    # Fallback to API Gateway REST API (Payload v1)
    if not method:
        method = event.get('httpMethod', 'GET')
    if not path:
        path = event.get('path', '/')

    return method.upper(), path

# ----------------- CRUD Operations -----------------

def get_all_students(query_params=None):
    """Retrieves all students, with optional query filters."""
    query_params = query_params or {}
    department = query_params.get('department')
    status = query_params.get('status')
    search = query_params.get('search', '').strip().lower()

    scan_kwargs = {}
    filter_expressions = []

    if department and department != 'All':
        filter_expressions.append(Attr('department').eq(department))
    if status and status != 'All':
        filter_expressions.append(Attr('status').eq(status))

    if filter_expressions:
        combined_filter = filter_expressions[0]
        for expr in filter_expressions[1:]:
            combined_filter = combined_filter & expr
        scan_kwargs['FilterExpression'] = combined_filter

    response = table.scan(**scan_kwargs)
    items = response.get('Items', [])

    # Handle DynamoDB scan pagination if there are more than 1MB of items
    while 'LastEvaluatedKey' in response:
        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = table.scan(**scan_kwargs)
        items.extend(response.get('Items', []))

    # Apply text search on name, student_id, or email if requested
    if search:
        items = [
            s for s in items
            if search in s.get('first_name', '').lower()
            or search in s.get('last_name', '').lower()
            or search in s.get('student_id', '').lower()
            or search in s.get('email', '').lower()
        ]

    # Sort students by creation date or name
    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return build_response(200, {
        'count': len(items),
        'students': items
    })

def get_student(student_id):
    """Fetches a single student by student_id."""
    response = table.get_item(Key={'student_id': student_id})
    item = response.get('Item')
    if not item:
        return build_response(404, {'error': f'Student with ID {student_id} not found.'})
    return build_response(200, {'student': item})

def create_student(data):
    """Creates a new student record."""
    required_fields = ['student_id', 'first_name', 'last_name', 'email', 'department']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return build_response(400, {'error': f'Missing required fields: {", ".join(missing)}'})

    student_id = str(data['student_id']).strip()

    # Check for existing record
    existing = table.get_item(Key={'student_id': student_id}).get('Item')
    if existing:
        return build_response(409, {'error': f'Student with ID {student_id} already exists.'})

    now = datetime.now(timezone.utc).isoformat()
    new_student = {
        'student_id': student_id,
        'first_name': str(data.get('first_name', '')).strip(),
        'last_name': str(data.get('last_name', '')).strip(),
        'email': str(data.get('email', '')).strip().lower(),
        'phone': str(data.get('phone', '')).strip(),
        'department': str(data.get('department', 'General')).strip(),
        'year': str(data.get('year', '1st Year')).strip(),
        'gpa': float_to_decimal(float(data.get('gpa', 0.0))),
        'status': str(data.get('status', 'Active')).strip(),
        'enrollment_date': str(data.get('enrollment_date', now[:10])),
        'courses': data.get('courses', []),
        'created_at': now,
        'updated_at': now
    }

    table.put_item(Item=new_student)
    return build_response(201, {'message': 'Student created successfully', 'student': new_student})

def update_student(student_id, data):
    """Updates an existing student's details."""
    existing = table.get_item(Key={'student_id': student_id}).get('Item')
    if not existing:
        return build_response(404, {'error': f'Student with ID {student_id} not found.'})

    now = datetime.now(timezone.utc).isoformat()

    # Build update expression
    update_fields = ['first_name', 'last_name', 'email', 'phone', 'department', 'year', 'gpa', 'status', 'enrollment_date', 'courses']
    update_parts = ['#updated_at = :updated_at']
    expr_names = {'#updated_at': 'updated_at'}
    expr_values = {':updated_at': now}

    for field in update_fields:
        if field in data:
            val = data[field]
            if field == 'gpa':
                val = float_to_decimal(float(val))
            expr_names[f'#{field}'] = field
            expr_values[f':{field}'] = val
            update_parts.append(f'#{field} = :{field}')

    update_expression = 'SET ' + ', '.join(update_parts)

    response = table.update_item(
        Key={'student_id': student_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
        ReturnValues='ALL_NEW'
    )

    return build_response(200, {
        'message': 'Student updated successfully',
        'student': response.get('Attributes')
    })

def delete_student(student_id):
    """Deletes a student record."""
    existing = table.get_item(Key={'student_id': student_id}).get('Item')
    if not existing:
        return build_response(404, {'error': f'Student with ID {student_id} not found.'})

    table.delete_item(Key={'student_id': student_id})
    return build_response(200, {'message': f'Student {student_id} deleted successfully.'})

def get_analytics():
    """Generates analytics summary: total count, department distribution, average GPA, status."""
    response = table.scan()
    items = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    total_students = len(items)
    if total_students == 0:
        return build_response(200, {
            'total_students': 0,
            'average_gpa': 0.0,
            'departments': {},
            'status_breakdown': {},
            'year_breakdown': {}
        })

    total_gpa = 0.0
    valid_gpa_count = 0
    dept_counts = {}
    status_counts = {}
    year_counts = {}

    for item in items:
        # GPA
        try:
            gpa = float(item.get('gpa', 0.0))
            if gpa > 0:
                total_gpa += gpa
                valid_gpa_count += 1
        except Exception:
            pass

        # Department
        dept = item.get('department', 'Unknown')
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

        # Status
        status = item.get('status', 'Active')
        status_counts[status] = status_counts.get(status, 0) + 1

        # Year
        year = item.get('year', 'Unknown')
        year_counts[year] = year_counts.get(year, 0) + 1

    avg_gpa = round(total_gpa / valid_gpa_count, 2) if valid_gpa_count > 0 else 0.0

    return build_response(200, {
        'total_students': total_students,
        'average_gpa': avg_gpa,
        'departments': dept_counts,
        'status_breakdown': status_counts,
        'year_breakdown': year_counts
    })

def seed_sample_data():
    """Seeds DynamoDB with realistic demo students if table is empty."""
    samples = [
        {
            "student_id": "STU-1001",
            "first_name": "Aarav",
            "last_name": "Sharma",
            "email": "aarav.sharma@university.edu",
            "phone": "+1-555-0101",
            "department": "Computer Science",
            "year": "3rd Year",
            "gpa": 3.88,
            "status": "Active",
            "enrollment_date": "2022-08-15",
            "courses": ["Cloud Computing", "Data Structures", "Operating Systems"]
        },
        {
            "student_id": "STU-1002",
            "first_name": "Sophia",
            "last_name": "Chen",
            "email": "sophia.chen@university.edu",
            "phone": "+1-555-0102",
            "department": "Electrical Engineering",
            "year": "4th Year",
            "gpa": 3.92,
            "status": "Active",
            "enrollment_date": "2021-08-20",
            "courses": ["Signals & Systems", "Digital Circuits", "Embedded Systems"]
        },
        {
            "student_id": "STU-1003",
            "first_name": "Marcus",
            "last_name": "Johnson",
            "email": "marcus.j@university.edu",
            "phone": "+1-555-0103",
            "department": "Mechanical Engineering",
            "year": "2nd Year",
            "gpa": 3.45,
            "status": "Active",
            "enrollment_date": "2023-08-18",
            "courses": ["Thermodynamics", "Statics", "CAD Design"]
        },
        {
            "student_id": "STU-1004",
            "first_name": "Ananya",
            "last_name": "Patel",
            "email": "ananya.patel@university.edu",
            "phone": "+1-555-0104",
            "department": "Data Science",
            "year": "3rd Year",
            "gpa": 3.75,
            "status": "Active",
            "enrollment_date": "2022-08-15",
            "courses": ["Machine Learning", "Data Mining", "Applied Statistics"]
        },
        {
            "student_id": "STU-1005",
            "first_name": "Liam",
            "last_name": "Smith",
            "email": "liam.smith@university.edu",
            "phone": "+1-555-0105",
            "department": "Business Administration",
            "year": "4th Year",
            "gpa": 3.60,
            "status": "Graduated",
            "enrollment_date": "2020-08-24",
            "courses": ["Corporate Finance", "Strategic Management", "Marketing Principles"]
        }
    ]

    seeded_count = 0
    now = datetime.now(timezone.utc).isoformat()
    for student in samples:
        existing = table.get_item(Key={'student_id': student['student_id']}).get('Item')
        if not existing:
            item = student.copy()
            item['gpa'] = float_to_decimal(item['gpa'])
            item['created_at'] = now
            item['updated_at'] = now
            table.put_item(Item=item)
            seeded_count += 1

    return build_response(200, {
        'message': f'Successfully seeded {seeded_count} student records.',
        'seeded_count': seeded_count
    })

# ----------------- Main Lambda Handler -----------------

def lambda_handler(event, context):
    """Main routing entrypoint for AWS Lambda."""
    method, path = extract_path_and_method(event)

    # Handle CORS preflight OPTIONS request
    if method == 'OPTIONS':
        return build_response(200, {'message': 'CORS preflight successful'})

    # Normalize path (remove trailing slash, split path parameters)
    clean_path = path.rstrip('/')
    path_parts = [p for p in clean_path.split('/') if p]

    # Query parameters
    query_params = event.get('queryStringParameters') or {}

    try:
        # Route: GET /analytics
        if path.endswith('/analytics') or path.endswith('/stats'):
            if method == 'GET':
                return get_analytics()

        # Route: POST /seed
        if path.endswith('/seed'):
            if method == 'POST':
                return seed_sample_data()

        # Route: /students or /students/{id}
        # Check if last segment is a student ID
        if len(path_parts) >= 2 and path_parts[-2] == 'students':
            student_id = path_parts[-1]
            if method == 'GET':
                return get_student(student_id)
            elif method == 'PUT':
                body = parse_body(event)
                return update_student(student_id, body)
            elif method == 'DELETE':
                return delete_student(student_id)

        # Route: /students
        if len(path_parts) >= 1 and path_parts[-1] == 'students':
            if method == 'GET':
                return get_all_students(query_params)
            elif method == 'POST':
                body = parse_body(event)
                return create_student(body)

        # Root route check / health check
        if path == '/' or clean_path == '':
            return build_response(200, {
                'service': 'Student Management System API',
                'status': 'healthy',
                'endpoints': [
                    'GET /students',
                    'POST /students',
                    'GET /students/{id}',
                    'PUT /students/{id}',
                    'DELETE /students/{id}',
                    'GET /analytics',
                    'POST /seed'
                ]
            })

        return build_response(404, {'error': f'Route not found: {method} {path}'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return build_response(500, {'error': str(e)})
