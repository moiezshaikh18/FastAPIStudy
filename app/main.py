from typing import Any
from fastapi import FastAPI, HTTPException, status
from app.schema.models import (
    Shipment,
    ShipmentUpdate,
    ShipmentStatus,
    CarrierChoice,
    Student,
    ContactDetail,
)

app = FastAPI(title="Shipment Management API")


# ==========================================
# In-Memory Database (Stores Pydantic objects)
# ==========================================

shipments: dict[int, Shipment] = {
    1: Shipment(
        id=1,
        recipient="Moiz Husain",
        phone="+919511843388",
        destination="Mumbai, India",
        status=ShipmentStatus.DELIVERED,
        items=["Mechanical Keyboard", "USB-C Hub"],
        weight_kg=1.4,
        carrier="BlueDart"
    ),
    2: Shipment(
        id=2,
        recipient="Ayaan Sharma",
        phone="+919876543210",
        destination="Bangalore, India",
        status=ShipmentStatus.IN_TRANSIT,
        items=["Ergonomic Mouse"],
        weight_kg=0.35,
        carrier="Delhivery"
    ),
    3: Shipment(
        id=3,
        recipient="Sara Khan",
        phone="+919123456789",
        destination="Delhi, India",
        status=ShipmentStatus.PENDING,
        items=["27-inch Monitor", "HDMI Cable"],
        weight_kg=6.8,
        carrier="FedEx"
    )
}

# In-memory database for students
students_db: dict[int, Student] = {}


# ==========================================
# API Endpoints (CRUD)
# ==========================================

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Shipment API!"}


# READ ALL
@app.get("/shipments", response_model=list[Shipment])
def get_all_shipments() -> list[Shipment]:
    """Returns a list of all shipments"""
    return list(shipments.values())


# SEARCH / FILTER (Multi-query parameters with Literal & Enum)
@app.get("/shipments/search", response_model=list[Shipment])
def filter_shipments(
    status: ShipmentStatus | None = None,
    carrier: CarrierChoice | None = None,
    city: str | None = None,
    max_weight: float | None = None
) -> list[Shipment]:
    """Filter shipments using query parameters (Status and Carrier have dropdowns!)"""
    return [
        s for s in shipments.values()
        if (status is None or s.status.lower() == status.lower())
        and (carrier is None or s.carrier.lower() == carrier.lower())
        and (city is None or city.lower() in s.destination.lower())
        and (max_weight is None or s.weight_kg <= max_weight)
    ]


# READ ONE
@app.get("/shipments/{id}", response_model=Shipment)
def get_shipment_by_id(id: int) -> Shipment:
    """Returns a single shipment by its ID"""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found"
        )
    return shipments[id]


# READ DYNAMIC FIELD
@app.get("/shipments/field/{field_name}")
def get_shipment_field(field_name: str, id: int) -> dict[str, Any]:
    """Dynamically get a specific field value of a shipment"""
    if id not in shipments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shipment {id} not found")
    
    shipment_dict = shipments[id].model_dump()
    if field_name not in shipment_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field '{field_name}' not found. Available: {list(shipment_dict.keys())}"
        )

    return {"id": id, "field": field_name, "value": shipment_dict[field_name]}


# CREATE (POST)
@app.post("/shipments", response_model=Shipment, status_code=status.HTTP_201_CREATED)
def create_shipment(payload: Shipment) -> Shipment:
    """
    Creates a new shipment.
    Pydantic automatically validates types, formats, and required fields!
    """
    if payload.id in shipments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Shipment with ID {payload.id} already exists."
        )

    shipments[payload.id] = payload
    return payload


# FULL UPDATE (PUT)
@app.put("/shipments/{id}", response_model=Shipment)
def update_shipment(id: int, payload: Shipment) -> Shipment:
    """Replaces an entire shipment"""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found."
        )

    payload.id = id
    shipments[id] = payload
    return payload


# PARTIAL UPDATE (PATCH)
@app.patch("/shipments/{id}", response_model=Shipment)
def patch_shipment(id: int, payload: ShipmentUpdate) -> Shipment:
    """Partially updates only the fields provided in the body"""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found."
        )

    existing_shipment = shipments[id]
    update_data = payload.model_dump(exclude_unset=True)
    updated_shipment = existing_shipment.model_copy(update=update_data)
    shipments[id] = updated_shipment

    return updated_shipment


# DELETE
@app.delete("/shipments/{id}")
def delete_shipment(id: int) -> dict[str, Any]:
    """Deletes a shipment by ID"""
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {id} not found."
        )

    deleted_item = shipments.pop(id)
    return {
        "message": f"Shipment {id} deleted successfully!",
        "deleted_item": deleted_item
    }


# ==========================================
# Student API Endpoints
# ==========================================

# CREATE Student (POST)
@app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED)
def create_student(payload: Student) -> Student:
    """
    Registers a new student.
    - Validates email domain and syntax
    - Validates phone (+91 and digit rules)
    - Validates CGPA (0.0 to 10.0)
    - Validates emergency contact for minors (<18)
    """
    if payload.id in students_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with ID {payload.id} already exists."
        )

    students_db[payload.id] = payload
    return payload


# GET all students
@app.get("/students", response_model=list[Student])
def get_all_students() -> list[Student]:
    """Returns all registered students"""
    return list(students_db.values())


# GET student by ID
@app.get("/students/{id}", response_model=Student)
def get_student_by_id(id: int) -> Student:
    """Returns a specific student by ID"""
    if id not in students_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {id} not found."
        )
    return students_db[id]
