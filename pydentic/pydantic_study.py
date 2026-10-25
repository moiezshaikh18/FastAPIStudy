"""
Pydantic Study & Demo Script
Demonstrates using models imported directly from app.schema.models.
Run this file directly using: python -m pydentic.pydantic_study
"""

from pydantic import ValidationError
from app.schema.models import Student, ContactDetail


# ==========================================
# DEMO EXECUTION
# ==========================================

if __name__ == "__main__":
    print("=== 1. Initialize Valid Student Object ===")

    student1 = Student(
        id=101,
        name="Moiz Husain",
        email="Moiz.Husain@GMAIL.com",                  # Automatically normalized to lowercase
        age=33,
        cgpa=8.75,
        interests=["Web Development", "AI", "Cloud Computing"],
        contact_detail=ContactDetail(
            phone="+919511843388",                     # Passes '+' and digit length validation
            city="Mumbai",
            emergency_contact="+919876543210"
        )
    )

    print("Student 1 (Successfully Created):")
    print(f"  Name : {student1.name}")
    print(f"  Email: {student1.email}")
    print(f"  Phone: {student1.contact_detail.phone}")
    print(f"  CGPA : {student1.cgpa}")
    print()

    print("=== 2. Test Phone Field Validator ===")
    try:
        # Invalid: Missing '+' country code prefix
        bad_phone = ContactDetail(
            phone="9511843388",
            city="Mumbai"
        )
    except ValidationError as e:
        print("[X] Phone validation error caught:")
        for err in e.errors():
            print(f" - {err['msg']}")

    print()
    print("=== 3. Test Email Field Validator ===")
    try:
        # Invalid: Uses a blocked disposable domain
        bad_email = Student(
            id=102,
            name="Ayaan",
            email="ayaan@tempmail.com",
            age=22
        )
    except ValidationError as e:
        print("[X] Email validation error caught:")
        for err in e.errors():
            print(f" - {err['msg']}")

    print()
    print("=== 4. Test Model Validator (Cross-Field Check) ===")
    try:
        # Invalid: Under 18 years old but emergency contact is missing
        underage_student = Student(
            id=104,
            name="Junior Ali",
            email="junior@gmail.com",
            age=16,
            contact_detail=ContactDetail(
                phone="+919511843388",
                city="Pune"
                # emergency_contact is omitted
            )
        )
    except ValidationError as e:
        print("[X] Model validator caught cross-field error:")
        for err in e.errors():
            print(f" - {err['msg']}")

    # Valid minor with emergency contact
    valid_minor = Student(
        id=105,
        name="Junior Ali",
        email="junior@gmail.com",
        age=16,
        contact_detail=ContactDetail(
            phone="+919511843388",
            city="Pune",
            emergency_contact="+919876543210"           # Provided!
        )
    )
    print(f"[OK] Minor with emergency contact passed: {valid_minor.name} (Age: {valid_minor.age})")
