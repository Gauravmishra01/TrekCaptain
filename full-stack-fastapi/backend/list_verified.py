#!/usr/bin/env python3
import boto3

client = boto3.client('ses', region_name='ap-south-1')
identities = client.list_identities()

print("Verified Email Addresses in SES:")
for i in identities.get('Identities', []):
    if '@' in i:
        print(f"  ✓ {i}")

print()
print("To receive emails from users, their email must be in this list.")
print("Or you need to verify the domain (gmail.com).")
