from typing import Any
from fastapi import FastAPI, HTTPException, status
from app.schema.models import (
    Shipment,
    ShipmentUpdate,
    ShipmentStatus,
    CarrierChoice,
    Student,
)
from app.database import shipments, save

# Initialize FastAPI application
app = FastAPI(
    title="Shipment & Student Management API",
    description="A beginner-friendly REST API demonstrating CRUD, Pydantic validation, Enums, and Literals.",
    version="1.0.0"
)

# In-memory database for students
students_db: dict[int, Student] = {}


# ==========================================
# Root Endpoint
# ==========================================

@app.get("/", tags=["General"])
def read_root() -> dict[str, str]:
    """Health check endpoint to verify server is running."""
    return {"message": "Welcome to the FastAPI Study API!"}


# ==========================================
# Shipment Endpoints (CRUD)
# ==========================================

# 1. READ ALL: Get list of all shipments
@app.get("/shipments", response_model=list[Shipment], tags=["Shipments"])
def get_all_shipments() -> list[Shipment]:
    """Returns a list of all existing shipments."""
    return list(shipments.values())


# 2. SEARCH & FILTER: Multi-query parameters with Enum and Literal dropdowns
# Note: Defined before /shipments/{id} to prevent path collision
@app.get("/shipments/search", response_model=list[Shipment], tags=["Shipments"])
def filter_shipments(
    status: ShipmentStatus | None = None,
    carrier: CarrierChoice | None = None,
    city: str | None = None,
    max_weight: float | None = None
) -> list[Shipment]:
    """
    Filters shipments using optional query parameters.
    - status: Choice from ShipmentStatus Enum
    - carrier: Choice from CarrierChoice Literal
    - city: Substring match on destination
    - max_weight: Upper limit for weight in kg
    """
    return [
        s for s in shipments.values()
        if (status is None or s["status"].lower() == status.lower())
        and (carrier is None or s["carrier"].lower() == carrier.lower())
        and (city is None or city.lower() in s["destination"].lower())
        and (max_weight is None or s["weight_kg"] <= max_weight)
    ]


# 3. READ ONE: Get shipment by unique ID
@app.get("/shipments/{id}", response_model=Shipment, tags=["Shipments"])
def get_shipment_by_id(id: int) -> Shipment:
    """Returns a single shipment by its ID (returns 404 if not found)."""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found."
        )
    return shipments[id]


# 4. READ FIELD: Dynamically fetch one specific field of a shipment
@app.get("/shipments/field/{field_name}", tags=["Shipments"])
def get_shipment_field(field_name: str, id: int) -> dict[str, Any]:
    """Fetches a specific field value (e.g. status, carrier, recipient) for a shipment."""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found."
        )
    
    shipment_dict = shipments[id]
    if field_name not in shipment_dict:
        available_fields = list(shipment_dict.keys())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field '{field_name}' not found. Available fields: {available_fields}"
        )

    return {"id": id, "field": field_name, "value": shipment_dict[field_name]}


# 5. CREATE (POST): Add a new shipment and save to JSON
@app.post("/shipments", response_model=Shipment, status_code=status.HTTP_201_CREATED, tags=["Shipments"])
def create_shipment(payload: Shipment) -> Shipment:
    """
    Creates a new shipment and permanently writes it to shipments.json.
    """
    if payload.id in shipments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Shipment with ID {payload.id} already exists."
        )

    # Save to in-memory dictionary and persist to JSON file
    new_data = payload.model_dump()
    shipments[payload.id] = new_data
    save()

    return payload


# 6. FULL UPDATE (PUT): Replace an entire shipment and save to JSON
@app.put("/shipments/{id}", response_model=Shipment, tags=["Shipments"])
def update_shipment(id: int, payload: Shipment) -> Shipment:
    """Replaces all fields of an existing shipment and persists to JSON."""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found."
        )

    # Keep URL ID consistent with model ID
    payload.id = id
    shipments[id] = payload.model_dump()
    save()

    return payload


# 7. PARTIAL UPDATE (PATCH): Update only the fields provided and save to JSON
@app.patch("/shipments/{id}", response_model=Shipment, tags=["Shipments"])
def patch_shipment(id: int, payload: ShipmentUpdate) -> Shipment:
    """Partially updates specified fields and persists to JSON."""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found."
        )

    # Update only the fields sent in request
    update_data = payload.model_dump(exclude_unset=True)
    shipments[id].update(update_data)
    save()

    return shipments[id]


# 8. DELETE: Remove a shipment by ID and save to JSON
@app.delete("/shipments/{id}", tags=["Shipments"])
def delete_shipment(id: int) -> dict[str, Any]:
    """Deletes a shipment by ID and saves changes to JSON."""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found."
        )

    deleted_item = shipments.pop(id)
    save()

    return {
        "message": f"Shipment {id} deleted successfully!",
        "deleted_item": deleted_item
    }


# ==========================================
# Student Endpoints
# ==========================================

# 1. CREATE Student (POST)
@app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED, tags=["Students"])
def create_student(payload: Student) -> Student:
    """
    Registers a new student.
    - Validates email syntax and blocks fake domains
    - Validates phone (+91 and digit rules)
    - Validates CGPA range (0.0 to 10.0)
    - Enforces emergency contact for students under 18
    """
    if payload.id in students_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with ID {payload.id} already exists."
        )

    students_db[payload.id] = payload
    return payload


# 2. READ ALL Students
@app.get("/students", response_model=list[Student], tags=["Students"])
def get_all_students() -> list[Student]:
    """Returns a list of all registered students."""
    return list(students_db.values())


# 3. READ ONE Student by ID
@app.get("/students/{id}", response_model=Student)
def get_student_by_id(id: int) -> Student:
    """Returns a single student by their ID."""
    if id not in students_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {id} not found."
        )
    return students_db[id]
