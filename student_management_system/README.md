# 🎓 Serverless Student Management System (AWS Free Tier)

An enterprise-ready, full-stack **Student Management System** built with a **100% AWS Free Tier** serverless architecture.

Designed for university evaluation, production demos, and cloud computing projects with **zero accidental costs**.

![Architecture: AWS Lambda + DynamoDB + API Gateway + S3](https://img.shields.io/badge/AWS-Serverless-FF9900?logo=amazon-aws&logoColor=white)
![Free Tier: $0/month](https://img.shields.io/badge/Cost-$0.00%2Fmo%20Free%20Tier-22c55e)
![Python 3.11+](https://img.shields.io/badge/Backend-Python%203.11+-3776ab?logo=python&logoColor=white)
![Status: Tested & Ready](https://img.shields.io/badge/Status-Tested%20%26%20Ready-6366f1)

---

## 🌟 Key Features

* **Complete Student Lifecycle Management (CRUD):**
  * Enroll new students with ID, name, email, department, academic year, GPA, and course lists.
  * Search students in real-time across name, student ID, and email.
  * Multi-dimensional filtering by Department (CS, EE, ME, Data Science, Business) and Status (Active, Graduated, Inactive, Suspended).
  * Edit student records and update course enrollments with automatic audit timestamps.
  * Delete records with confirmation dialogue.
* **Interactive Analytics & KPI Dashboard:**
  * Real-time metrics: Total Enrolled, Active Students, Average GPA.
  * Visual breakdowns: Department distribution doughnut chart and class status bar chart powered by Chart.js.
* **CSV Data Export:** One-click download of student records into standard CSV format for offline reporting.
* **Dual-Mode Connectivity (Cloud & Local):**
  * **AWS Cloud Mode:** Directly calls your live AWS API Gateway and writes to Amazon DynamoDB.
  * **Local / Demo Mode:** Runs immediately out of the box with zero setup using the included zero-dependency Python server or browser local cache.
* **Built-in Free Tier Cost Guardrails:**
  * Only utilizes serverless resources that incur **$0.00 when idle**.
  * Automated cleanup script (`python3 aws/cleanup.py`) to tear down cloud resources anytime.

---

## 🏛️ System Architecture

```
                                  [ Web Browser Client ]
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       │                                           │
             (1) Web Page Assets                        (2) REST API Calls
                       │                                           │
                       ▼                                           ▼
             ┌──────────────────┐                       ┌─────────────────────┐
             │    Amazon S3     │                       │ Amazon API Gateway  │
             │  Static Hosting  │                       │   (HTTP API v2)     │
             │   (5 GB Free)    │                       │  (1M Calls Free/mo) │
             └──────────────────┘                       └──────────┬──────────┘
                                                                   │
                                                                   ▼
                                                        ┌─────────────────────┐
                                                        │     AWS Lambda      │
                                                        │  (Python Handler)   │
                                                        │  (1M Invocations)   │
                                                        └──────────┬──────────┘
                                                                   │
                                                                   ▼
                                                        ┌─────────────────────┐
                                                        │   Amazon DynamoDB   │
                                                        │  (Students Table)   │
                                                        │ (25 GB Always Free) │
                                                        └─────────────────────┘
```

Detailed architecture diagrams and IAM security policies can be found in [ARCHITECTURE.md](file:///Users/apple/Downloads/student_management_system/ARCHITECTURE.md).

---

## 💰 AWS Free Tier Breakdown

| Component | AWS Free Tier Quota | Project Consumption | Cost |
| :--- | :--- | :--- | :--- |
| **AWS Lambda** | 1,000,000 requests / month | ~500 - 2,000 requests | **$0.00** |
| **Amazon DynamoDB** | **25 GB** storage & 25 WCU/RCU (**Always Free**) | < 1 MB | **$0.00** |
| **Amazon API Gateway** | 1,000,000 HTTP API calls / month | ~500 - 2,000 calls | **$0.00** |
| **Amazon S3** | 5 GB Standard Storage | < 2 MB | **$0.00** |
| **CloudWatch Logs** | 5 GB Log Data Ingestion | < 5 MB | **$0.00** |
| **Total** | | | **$0.00 / month** |

---

## 📁 Project Structure

```
student_management_system/
├── backend/
│   ├── lambda_function.py      # Core AWS Lambda handler (CRUD, Analytics, DynamoDB logic)
│   └── test_lambda.py          # Unit tests simulating API Gateway events (6/6 passing)
├── frontend/
│   ├── index.html              # Modern responsive student dashboard UI
│   ├── app.js                  # Frontend client, API caller, charts, and modals
│   ├── style.css               # Styling and visual polish
│   └── config.js               # API Gateway endpoint URL configuration
├── aws/
│   ├── cloudformation.yaml     # 1-Click AWS CloudFormation template
│   ├── deploy.py               # 1-Command automated AWS Python deployment script
│   └── cleanup.py              # 1-Command teardown script (guarantees $0 cost)
├── local_server.py             # Zero-dependency local mock server for offline testing
├── test_local_logic.py         # Test suite verifying local database operations
├── sample_data.json            # Initial sample student records for demonstration
├── requirements.txt            # Optional boto3 requirement for deploy script
├── ARCHITECTURE.md             # Deep-dive architecture and sequence diagrams
└── README.md                   # This project guide
```

---

## 🚀 Quickstart Guide

### Option 1: Run Locally (Zero Setup, Instant Preview)

You can run and test the complete system right on your machine right now—without needing an AWS account or pip installations:

```bash
# Start the local server
python3 local_server.py
```

1. Open your browser to: **`http://localhost:8000`**
2. You will see the full dashboard pre-seeded with students!
3. Add, edit, filter, view, or delete students.
4. Changes are persisted in `local_db.json`.

---

### Option 2: Automated 1-Click AWS Cloud Deployment

When you want to deploy the live backend to your actual AWS account:

#### 1. Set your AWS Credentials
Run in your terminal:
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### 2. Install boto3 (if not installed)
```bash
pip3 install -r requirements.txt
```

#### 3. Run the automated deployer
```bash
python3 aws/deploy.py
```

The script will automatically:
1. Create the DynamoDB table `StudentManagementTable` with Free-Tier billing.
2. Create the IAM Role `StudentManagementLambdaRole` with least-privilege policies.
3. Package and deploy the AWS Lambda function `StudentManagementApi`.
4. Create the Amazon API Gateway HTTP API with CORS enabled.
5. Grant API Gateway invocation permissions to Lambda.
6. Automatically test the live endpoint and write the new API URL into `frontend/config.js`!

---

### Option 3: Deploy via AWS Management Console (CloudFormation)

If you prefer using the official AWS Web Console:

1. Log into the [AWS Management Console](https://console.aws.amazon.com/).
2. Navigate to **CloudFormation** → Click **Create stack** → **With new resources (standard)**.
3. Select **Upload a template file** → Choose [aws/cloudformation.yaml](file:///Users/apple/Downloads/student_management_system/aws/cloudformation.yaml).
4. Enter Stack Name: `student-management-system` → Click **Next** → Click **Next** → Check *"I acknowledge that AWS CloudFormation might create IAM resources"* → Click **Submit**.
5. Once complete (in ~60 seconds), go to the **Outputs** tab to view your live `ApiEndpointUrl`!
6. Paste the URL into `frontend/config.js` or directly into the UI via the **Backend Settings** button.

---

## 📡 REST API Reference

All endpoints return JSON and include standard CORS headers (`Access-Control-Allow-Origin: *`).

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/students` | List all students. Supports query params: `?department=CS&status=Active&search=John` |
| `GET` | `/students/{id}` | Get detailed profile of a specific student by ID |
| `POST` | `/students` | Create a new student record (JSON body required) |
| `PUT` | `/students/{id}` | Update student attributes (GPA, status, courses, etc.) |
| `DELETE` | `/students/{id}` | Delete student record from DynamoDB |
| `GET` | `/analytics` | Get summary counts, department distribution, and average GPA |
| `POST` | `/seed` | Populate DynamoDB with demo sample records |

### Sample POST Request Body (`/students`)
```json
{
  "student_id": "STU-2005",
  "first_name": "Maya",
  "last_name": "Lin",
  "email": "maya.lin@university.edu",
  "phone": "+1-555-0188",
  "department": "Computer Science",
  "year": "2nd Year",
  "gpa": 3.92,
  "status": "Active",
  "enrollment_date": "2024-01-15",
  "courses": ["Cloud Computing", "Algorithms", "Linear Algebra"]
}
```

---

## 🧪 Running the Tests

To verify that the Lambda handler and database logic are functioning properly:

```bash
# Run AWS Lambda handler unit tests (6 tests, mocks API Gateway & DynamoDB)
python3 backend/test_lambda.py

# Run local database logic tests
python3 test_local_logic.py
```

---

## 🧹 Tear Down & Cost Protection

Whenever your project presentation or evaluation is finished, you can safely remove all cloud resources with one command:

```bash
python3 aws/cleanup.py
```

This immediately deletes the API Gateway, Lambda function, IAM role, and DynamoDB table, guaranteeing that your AWS account remains clean and free of charges.
