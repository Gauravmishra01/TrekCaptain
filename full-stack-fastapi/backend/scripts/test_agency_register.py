#!/usr/bin/env python3
"""Test helper to call the AgencyRegistration endpoint function directly.

This imports the Pydantic model and function and executes it locally so we can
see errors before running via HTTP/uvicorn.
"""
import json
import traceback

from app.three_sides_api.routers import agency
from app.three_sides_api.routers.agency import AgencyRegistration


def main():
    payload = AgencyRegistration(
        legal_name="Test Agency Pvt Ltd",
        trade_name="TestAgency",
        country="India",
        business_address="123 Test Street, Shimla",
        entity_type="Private Limited Company",
        primary_category="Adventure",
        inventory_focus=["Paragliding", "River Rafting"],
        technical_need="Web Portal Access ONLY",
        gstin="12ABCDE1234F2Z5",
        pan="ABCDE1234F",
        bank_account="1234567890",
        initial_deposit=10000.5,
        contact_name="Amit Kumar",
        contact_designation="Head Partnerships",
        contact_email="amit@example.com",
        contact_mobile="+911234567890",
    )

    try:
        result = agency.register_agency(payload)
        print("Result:", json.dumps(result, indent=2))
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
