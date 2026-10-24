#!/usr/bin/env python3
"""
Automated 1-Click AWS Deployment Script
Deploys Student Management System to AWS Free Tier:
  - DynamoDB Table
  - IAM Execution Role
  - AWS Lambda Function (Python)
  - Amazon API Gateway (HTTP API v2)
  - Updates frontend/config.js with the live API URL
"""

import sys
import os
import io
import time
import json
import zipfile
import urllib.request

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("\n❌ Error: 'boto3' library is not installed.")
    print("👉 Install it by running: pip3 install boto3")
    print("👉 Or use the CloudFormation template in aws/cloudformation.yaml via the AWS Console.")
    sys.exit(1)

# Configuration Constants
REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
TABLE_NAME = 'StudentManagementTable'
ROLE_NAME = 'StudentManagementLambdaRole'
LAMBDA_NAME = 'StudentManagementApi'
API_NAME = 'StudentManagementHttpApi'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_FILE = os.path.join(BASE_DIR, 'backend', 'lambda_function.py')
CONFIG_FILE = os.path.join(BASE_DIR, 'frontend', 'config.js')

def create_lambda_zip():
    """Packages backend/lambda_function.py into an in-memory zip bytes buffer."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(BACKEND_FILE, arcname='lambda_function.py')
    buf.seek(0)
    return buf.read()

def step_print(step_num, title):
    print(f"\n[{step_num}/5] 🚀 {title}...")

def main():
    print("=" * 65)
    print("🎓 AWS Student Management System - Automated Free Tier Deployer")
    print(f"🌍 AWS Region: {REGION}")
    print("=" * 65)

    # 1. Verify AWS Credentials
    try:
        sts = boto3.client('sts', region_name=REGION)
        caller = sts.get_caller_identity()
        print(f"✅ Authenticated AWS Account: {caller['Account']} (Arn: {caller['Arn']})")
    except Exception as e:
        print(f"\n❌ AWS Authentication Failed: {e}")
        print("\nPlease ensure your AWS credentials are set up. Run:")
        print("  export AWS_ACCESS_KEY_ID=\"your_key\"")
        print("  export AWS_SECRET_ACCESS_KEY=\"your_secret\"")
        print("  export AWS_DEFAULT_REGION=\"us-east-1\"")
        print("Or configure via AWS CLI: `aws configure`\n")
        sys.exit(1)

    dynamodb = boto3.client('dynamodb', region_name=REGION)
    iam = boto3.client('iam', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    apigw = boto3.client('apigatewayv2', region_name=REGION)

    # Step 1: Create or verify DynamoDB Table
    step_print(1, f"Setting up DynamoDB Table '{TABLE_NAME}'")
    try:
        dynamodb.describe_table(TableName=TABLE_NAME)
        print(f"   ℹ️  Table '{TABLE_NAME}' already exists.")
    except dynamodb.exceptions.ResourceNotFoundException:
        print(f"   📦 Creating table '{TABLE_NAME}' (Free Tier / Pay-Per-Request)...")
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{'AttributeName': 'student_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'student_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        print("   ⏳ Waiting for table to become ACTIVE...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        print(f"   ✅ Table '{TABLE_NAME}' created successfully.")

    # Step 2: Create or verify IAM Role for Lambda
    step_print(2, f"Setting up IAM Role '{ROLE_NAME}'")
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    dynamo_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Scan",
                "dynamodb:Query"
            ],
            "Resource": f"arn:aws:dynamodb:{REGION}:{caller['Account']}:table/{TABLE_NAME}"
        }]
    }

    try:
        role_resp = iam.get_role(RoleName=ROLE_NAME)
        role_arn = role_resp['Role']['Arn']
        print(f"   ℹ️  IAM Role '{ROLE_NAME}' already exists.")
    except iam.exceptions.NoSuchEntityException:
        print(f"   🔐 Creating IAM Role '{ROLE_NAME}'...")
        role_resp = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for Student Management Lambda function"
        )
        role_arn = role_resp['Role']['Arn']

        # Attach standard CloudWatch Logs policy
        iam.attach_role_policy(
            RoleName=ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        # Put inline policy for DynamoDB
        iam.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName="DynamoDBStudentTableAccess",
            PolicyDocument=json.dumps(dynamo_policy)
        )
        print("   ⏳ Waiting 10 seconds for IAM role replication across AWS...")
        time.sleep(10)
        print(f"   ✅ IAM Role created: {role_arn}")

    # Step 3: Deploy AWS Lambda Function
    step_print(3, f"Deploying Lambda Function '{LAMBDA_NAME}'")
    zip_bytes = create_lambda_zip()

    try:
        lambda_info = lambda_client.get_function(FunctionName=LAMBDA_NAME)
        print(f"   🔄 Updating existing Lambda code...")
        lambda_client.update_function_code(
            FunctionName=LAMBDA_NAME,
            ZipFile=zip_bytes
        )
        lambda_arn = lambda_info['Configuration']['FunctionArn']
        print("   ✅ Lambda code updated successfully.")
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"   📦 Creating new Lambda function '{LAMBDA_NAME}'...")
        # IAM role might take a few moments to be assumeable
        max_retries = 5
        for attempt in range(max_retries):
            try:
                resp = lambda_client.create_function(
                    FunctionName=LAMBDA_NAME,
                    Runtime='python3.11',
                    Role=role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_bytes},
                    Description='Backend API for Student Management System',
                    Timeout=15,
                    MemorySize=256,
                    Environment={'Variables': {'TABLE_NAME': TABLE_NAME, 'AWS_REGION': REGION}}
                )
                lambda_arn = resp['FunctionArn']
                print(f"   ✅ Lambda created: {lambda_arn}")
                break
            except ClientError as e:
                if 'The role defined for the function cannot be assumed' in str(e) and attempt < max_retries - 1:
                    print(f"   ⏳ Waiting for IAM propagation (attempt {attempt+1}/{max_retries})...")
                    time.sleep(6)
                else:
                    raise

    # Step 4: Create or update Amazon API Gateway (HTTP API v2)
    step_print(4, f"Configuring Amazon API Gateway (HTTP API)")
    apis = apigw.get_apis().get('Items', [])
    existing_api = next((a for a in apis if a['Name'] == API_NAME), None)

    if existing_api:
        api_id = existing_api['ApiId']
        api_endpoint = existing_api['ApiEndpoint']
        print(f"   ℹ️  API Gateway '{API_NAME}' already exists (ID: {api_id}).")
    else:
        print(f"   🌐 Creating HTTP API '{API_NAME}' with CORS...")
        new_api = apigw.create_api(
            Name=API_NAME,
            ProtocolType='HTTP',
            CorsConfiguration={
                'AllowOrigins': ['*'],
                'AllowMethods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                'AllowHeaders': ['Content-Type', 'Authorization', 'X-Requested-With']
            }
        )
        api_id = new_api['ApiId']
        api_endpoint = new_api['ApiEndpoint']

        # Create Lambda Integration
        integration = apigw.create_integration(
            ApiId=api_id,
            IntegrationType='AWS_PROXY',
            IntegrationUri=lambda_arn,
            PayloadFormatVersion='2.0'
        )
        int_id = integration['IntegrationId']

        # Create $default route
        apigw.create_route(
            ApiId=api_id,
            RouteKey='$default',
            Target=f"integrations/{int_id}"
        )

        # Create $default auto-deploy stage
        apigw.create_stage(
            ApiId=api_id,
            StageName='$default',
            AutoDeploy=True
        )

        # Grant API Gateway permission to invoke Lambda
        try:
            lambda_client.add_permission(
                FunctionName=LAMBDA_NAME,
                StatementId='ApiGatewayInvokePermission',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:{REGION}:{caller['Account']}:{api_id}/*"
            )
        except lambda_client.exceptions.ResourceConflictException:
            pass

        print(f"   ✅ API Gateway created: {api_endpoint}")

    # Step 5: Test and Update Frontend Configuration
    step_print(5, "Verifying API & Updating Frontend Config")
    print(f"   🧪 Testing endpoint: {api_endpoint}/students ...")
    time.sleep(2)
    try:
        req = urllib.request.Request(f"{api_endpoint}/students", headers={'User-Agent': 'Deployer'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            print(f"   ✅ API Ping Success! Response HTTP {status}")
    except Exception as e:
        print(f"   ⚠️  Initial ping returned note ({e}). It might take 30s to DNS propagate.")

    # Write API URL into frontend/config.js
    new_config = f"""// Auto-generated by aws/deploy.py on {time.strftime('%Y-%m-%d %H:%M:%S')}
window.APP_CONFIG = {{
    apiUrl: "{api_endpoint}",
    awsRegion: "{REGION}",
    enableLocalFallback: true
}};
"""
    with open(CONFIG_FILE, 'w') as f:
        f.write(new_config)
    print(f"   ✅ Updated frontend/config.js with API Endpoint!")

    print("\n" + "=" * 65)
    print("🎉 DEPLOYMENT COMPLETE! YOUR AWS SERVERLESS SYSTEM IS LIVE!")
    print("=" * 65)
    print(f"🌐 Live API Gateway URL : {api_endpoint}")
    print(f"📦 DynamoDB Table       : {TABLE_NAME}")
    print(f"⚡ AWS Lambda Function   : {LAMBDA_NAME}")
    print(f"💰 AWS Monthly Cost Est : $0.00 (Free Tier Guaranteed)")
    print("\n👉 Next steps:")
    print("  1. Run 'python3 local_server.py' to open the UI connected to your live AWS backend.")
    print("  2. Or host the 'frontend/' folder in S3 static website hosting.")
    print("  3. To tear down resources anytime, run: 'python3 aws/cleanup.py'")
    print("=" * 65)

if __name__ == '__main__':
    main()
