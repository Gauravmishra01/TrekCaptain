#!/usr/bin/env python3
"""Simple DynamoDB debug helper to fetch a user by user_id.

Usage:
  python get_user_debug.py <user_id>

This script uses the default boto3 session/credentials and region.
It prints the DynamoDB item (if any) for `TravelAppUsers`.
"""
import sys
import json
import boto3
from botocore.exceptions import ClientError


def get_dynamodb_resource(region_name: str | None = None):
    session = boto3.Session()
    # If AWS_REGION env var present boto3 will pick it up; allow override
    return session.resource("dynamodb", region_name=region_name)


def fetch_user(user_id: str):
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table("TravelAppUsers")
    try:
        resp = table.get_item(Key={"user_id": user_id})
        return resp.get("Item")
    except ClientError as exc:
        print("DynamoDB ClientError:", exc.response.get("Error", {}).get("Message", str(exc)))
        raise


def main():
    if len(sys.argv) < 2:
        print("Usage: python get_user_debug.py <user_id>")
        sys.exit(2)

    user_id = sys.argv[1]
    print(f"Checking TravelAppUsers for user_id={user_id}...")
    item = fetch_user(user_id)
    if not item:
        print("User not found")
        sys.exit(1)

    print("Found user:")
    print(json.dumps(item, indent=2, default=str))


if __name__ == "__main__":
    main()
