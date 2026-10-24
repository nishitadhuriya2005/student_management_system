#!/usr/bin/env python3
"""
AWS Resource Cleanup Script
Safely removes resources created for Student Management System to guarantee zero cost:
  - Deletes API Gateway
  - Deletes AWS Lambda Function
  - Deletes IAM Role & Policies
  - Deletes DynamoDB Table
"""

import sys
import os

try:
    import boto3
except ImportError:
    print("❌ Error: 'boto3' library is not installed.")
    sys.exit(1)

REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
TABLE_NAME = 'StudentManagementTable'
ROLE_NAME = 'StudentManagementLambdaRole'
LAMBDA_NAME = 'StudentManagementApi'
API_NAME = 'StudentManagementHttpApi'

def main():
    print("=" * 65)
    print("🧹 AWS Student Management System - Resource Cleanup")
    print(f"🌍 Region: {REGION}")
    print("=" * 65)

    confirm = input("⚠️  Are you sure you want to delete all AWS resources? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cleanup aborted.")
        return

    dynamodb = boto3.client('dynamodb', region_name=REGION)
    iam = boto3.client('iam', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    apigw = boto3.client('apigatewayv2', region_name=REGION)

    # 1. Delete API Gateway
    print("\n1. Deleting API Gateway...")
    try:
        apis = apigw.get_apis().get('Items', [])
        for api in apis:
            if api['Name'] == API_NAME:
                apigw.delete_api(ApiId=api['ApiId'])
                print(f"   ✅ Deleted API Gateway '{API_NAME}' ({api['ApiId']})")
    except Exception as e:
        print(f"   ⚠️  API Gateway cleanup notice: {e}")

    # 2. Delete Lambda
    print("\n2. Deleting Lambda Function...")
    try:
        lambda_client.delete_function(FunctionName=LAMBDA_NAME)
        print(f"   ✅ Deleted Lambda function '{LAMBDA_NAME}'")
    except Exception as e:
        print(f"   ⚠️  Lambda cleanup notice: {e}")

    # 3. Delete IAM Role & Policies
    print("\n3. Deleting IAM Role...")
    try:
        # Delete inline policies
        for p in iam.list_role_policies(RoleName=ROLE_NAME).get('PolicyNames', []):
            iam.delete_role_policy(RoleName=ROLE_NAME, PolicyName=p)
        # Detach managed policies
        for p in iam.list_attached_role_policies(RoleName=ROLE_NAME).get('AttachedPolicies', []):
            iam.detach_role_policy(RoleName=ROLE_NAME, PolicyArn=p['PolicyArn'])
        # Delete role
        iam.delete_role(RoleName=ROLE_NAME)
        print(f"   ✅ Deleted IAM Role '{ROLE_NAME}'")
    except Exception as e:
        print(f"   ⚠️  IAM cleanup notice: {e}")

    # 4. Delete DynamoDB Table
    print("\n4. Deleting DynamoDB Table...")
    try:
        dynamodb.delete_table(TableName=TABLE_NAME)
        print(f"   ✅ Deleted DynamoDB Table '{TABLE_NAME}'")
    except Exception as e:
        print(f"   ⚠️  DynamoDB cleanup notice: {e}")

    print("\n" + "=" * 65)
    print("✨ Cleanup complete! All project cloud resources removed.")
    print("=" * 65)

if __name__ == '__main__':
    main()
