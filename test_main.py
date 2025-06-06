import pytest
from fastapi.testclient import TestClient
import os
import sqlite3
from datetime import datetime
import pytz

# Import the app and functions
import sys
sys.path.append('.')

def get_app():
    """Import app dynamically to avoid circular imports"""
    from main import app
    return app

def get_init_db():
    """Import init_db function dynamically"""
    from main import init_db
    return init_db

client = TestClient(get_app())

@pytest.fixture(scope="function")
def setup_test_db():
    """Setup test database for each test"""
    # Use a separate test database
    test_db = "test_fitness_studio.db"
    
    # Remove existing test db if exists
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Temporarily change the database URL for testing
    import main
    original_db = main.DATABASE_URL
    main.DATABASE_URL = test_db
    
    # Initialize test database
    init_db = get_init_db()
    init_db()
    
    yield test_db
    
    # Cleanup
    main.DATABASE_URL = original_db
    if os.path.exists(test_db):
        os.remove(test_db)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Fitness Studio Booking API" in response.json()["message"]

def test_get_classes(setup_test_db):
    """Test getting all classes"""
    response = client.get("/classes")
    assert response.status_code == 200
    classes = response.json()
    assert len(classes) > 0
    
    # Check class structure
    first_class = classes[0]
    required_fields = ["id", "name", "instructor", "datetime", "total_slots", "available_slots"]
    for field in required_fields:
        assert field in first_class

def test_get_classes_with_timezone(setup_test_db):
    """Test getting classes with different timezone"""
    response = client.get("/classes?timezone=UTC")
    assert response.status_code == 200
    classes = response.json()
    assert len(classes) > 0

def test_book_class_success(setup_test_db):
    """Test successful class booking"""
    # First get available classes
    classes_response = client.get("/classes")
    classes = classes_response.json()
    assert len(classes) > 0
    
    class_id = classes[0]["id"]
    
    # Make a booking
    booking_data = {
        "class_id": class_id,
        "client_name": "John Doe",
        "client_email": "john.doe@example.com"
    }
    
    response = client.post("/book", json=booking_data)
    assert response.status_code == 200
    
    booking_result = response.json()
    assert booking_result["message"] == "Booking successful"
    assert "booking_id" in booking_result
    assert booking_result["client_name"] == "John Doe"

def test_book_nonexistent_class(setup_test_db):
    """Test booking a non-existent class"""
    booking_data = {
        "class_id": 999,
        "client_name": "John Doe",
        "client_email": "john.doe@example.com"
    }
    
    response = client.post("/book", json=booking_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_duplicate_booking(setup_test_db):
    """Test preventing duplicate bookings"""
    # Get a class
    classes_response = client.get("/classes")
    classes = classes_response.json()
    class_id = classes[0]["id"]
    
    booking_data = {
        "class_id": class_id,
        "client_name": "Jane Doe",
        "client_email": "jane.doe@example.com"
    }
    
    # First booking
    response1 = client.post("/book", json=booking_data)
    assert response1.status_code == 200
    
    # Second booking (should fail)
    response2 = client.post("/book", json=booking_data)
    assert response2.status_code == 400
    assert "already booked" in response2.json()["detail"].lower()

def test_invalid_booking_data(setup_test_db):
    """Test booking with invalid data"""
    # Missing required fields
    response = client.post("/book", json={})
    assert response.status_code == 422
    
    # Invalid email
    booking_data = {
        "class_id": 1,
        "client_name": "John Doe",
        "client_email": "not-an-email"
    }
    response = client.post("/book", json=booking_data)
    assert response.status_code == 422
    
    # Empty name
    booking_data = {
        "class_id": 1,
        "client_name": "",
        "client_email": "john.doe@example.com"
    }
    response = client.post("/book", json=booking_data)
    assert response.status_code == 422

def test_get_bookings(setup_test_db):
    """Test getting bookings for a user"""
    # First make a booking
    classes_response = client.get("/classes")
    classes = classes_response.json()
    class_id = classes[0]["id"]
    
    booking_data = {
        "class_id": class_id,
        "client_name": "Alice Smith",
        "client_email": "alice.smith@example.com"
    }
    
    client.post("/book", json=booking_data)
    
    # Get bookings
    response = client.get("/bookings?email=alice.smith@example.com")
    assert response.status_code == 200
    
    bookings = response.json()
    assert len(bookings) == 1
    assert bookings[0]["client_email"] == "alice.smith@example.com"
    assert bookings[0]["class_id"] == class_id

def test_get_bookings_empty(setup_test_db):
    """Test getting bookings for user with no bookings"""
    response = client.get("/bookings?email=nonexistent@example.com")
    assert response.status_code == 200
    assert response.json() == []

def test_available_slots_decrease(setup_test_db):
    """Test that available slots decrease after booking"""
    # Get initial class info
    classes_response = client.get("/classes")
    classes = classes_response.json()
    class_id = classes[0]["id"]
    initial_slots = classes[0]["available_slots"]
    
    # Make a booking
    booking_data = {
        "class_id": class_id,
        "client_name": "Bob Johnson",
        "client_email": "bob.johnson@example.com"
    }
    
    client.post("/book", json=booking_data)
    
    # Check slots decreased
    classes_response = client.get("/classes")
    updated_classes = classes_response.json()
    updated_class = next(c for c in updated_classes if c["id"] == class_id)
    
    assert updated_class["available_slots"] == initial_slots - 1

if __name__ == "__main__":
    pytest.main(["-v"])