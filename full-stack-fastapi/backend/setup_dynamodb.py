#!/usr/bin/env python3
"""
Script to create DynamoDB tables for TravelApp:
  1. TravelAppUsers - Main user table
  2. OTPVerification - OTP verification codes with expiration

Usage:
    python setup_dynamodb.py
"""

import boto3
from botocore.exceptions import ClientError


def create_travel_app_users_table():
    """Create the TravelAppUsers DynamoDB table if it doesn't exist."""
    
    dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
    table_name = "TravelAppUsers"
    
    try:
        table = dynamodb.Table(table_name)
        table.load()
        print(f"✓ Table '{table_name}' already exists.")
        print(f"  Status: {table.table_status}")
        return True
        
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Table '{table_name}' not found. Creating...")
            
            try:
                table = dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {"AttributeName": "user_id", "KeyType": "HASH"}
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "user_id", "AttributeType": "S"}
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
                
                print(f"✓ Table '{table_name}' created successfully!")
                print(f"  Region: ap-south-1")
                print(f"  Partition Key: user_id")
                
                table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
                print(f"✓ Table is now active and ready to use.")
                return True
                
            except ClientError as create_error:
                print(f"✗ Error creating table: {create_error}")
                return False
        else:
            print(f"✗ Error: {e}")
            return False


def create_otp_verification_table():
    """Create the OTPVerification DynamoDB table if it doesn't exist."""
    
    dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
    client = boto3.client("dynamodb", region_name="ap-south-1")
    table_name = "OTPVerification"
    
    try:
        table = dynamodb.Table(table_name)
        table.load()
        print(f"✓ Table '{table_name}' already exists.")
        print(f"  Status: {table.table_status}")
        return True
        
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Table '{table_name}' not found. Creating...")
            
            try:
                table = dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {"AttributeName": "phone_number", "KeyType": "HASH"}
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "phone_number", "AttributeType": "S"}
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
                
                print(f"✓ Table '{table_name}' created successfully!")
                print(f"  Region: ap-south-1")
                print(f"  Partition Key: phone_number")
                
                table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
                print(f"✓ Table is now active.")
                
                # Enable TTL on the table
                try:
                    client.update_time_to_live(
                        TableName=table_name,
                        TimeToLiveSpecification={
                            "Enabled": True,
                            "AttributeName": "expiration"
                        }
                    )
                    print(f"✓ TTL enabled on 'expiration' attribute (auto-delete after 5 minutes)")
                except ClientError as ttl_error:
                    if "ValidationException" in str(ttl_error):
                        print(f"⚠ TTL already configured or pending update")
                    else:
                        print(f"⚠ Warning enabling TTL: {ttl_error}")
                
                return True
                
            except ClientError as create_error:
                print(f"✗ Error creating table: {create_error}")
                return False
        else:
            print(f"✗ Error: {e}")
            return False


if __name__ == "__main__":
    print("=" * 70)
    print("DynamoDB Tables Setup for TravelApp")
    print("=" * 70)
    
    success1 = create_travel_app_users_table()
    print()
    success2 = create_otp_verification_table()
    
    print("=" * 70)
    if success1 and success2:
        print("✓ All tables created successfully! You can now start the FastAPI server.")
    else:
        print("✗ Some tables failed to create. Please check your AWS credentials and region.")
