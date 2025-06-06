# Fitness_Studio_API

# Fitness Studio Booking API

A comprehensive REST API for managing fitness class bookings with timezone support, built with FastAPI and SQLite.

##  Features

- **Class Management**: View all upcoming fitness classes with instructor details
- **Smart Booking System**: Book classes with automatic slot management
- **Timezone Support**: Classes stored in IST, convertible to any timezone
- **Duplicate Prevention**: Prevents users from booking the same class twice
- **Email-based Booking History**: Retrieve all bookings for a specific email
- **Input Validation**: Comprehensive validation for all inputs
- **Error Handling**: Proper error responses with meaningful messages
- **Logging**: Detailed logging for debugging and monitoring

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLite**: Lightweight database for data persistence
- **Pydantic**: Data validation and settings management
- **Pytz**: Timezone handling
- **Pytest**: Unit testing framework

## Project Structure

```
fitness-studio-api/
├── main.py              # Main application file
├── test_main.py         # Unit tests
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── fitness_studio.db   # SQLite database (created automatically)
└── sample_requests.json # Sample API requests
```

## Setup Instructions

### 1. Clone or Download the Project

```bash
# Create project directory
mkdir fitness-studio-api
cd fitness-studio-api

# Copy the provided files into this directory
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Start the server
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 5. View API Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

##  API Endpoints

### 1. Get All Classes
```http
GET /classes?timezone=Asia/Kolkata
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Yoga Flow",
    "instructor": "Priya Sharma",
    "datetime": "2025-06-09T07:00:00+05:30",
    "total_slots": 20,
    "available_slots": 20
  }
]
```

### 2. Book a Class
```http
POST /book
Content-Type: application/json

{
  "class_id": 1,
  "client_name": "John Doe",
  "client_email": "john.doe@example.com"
}
```

**Response:**
```json
{
  "message": "Booking successful",
  "booking_id": 1,
  "class_name": "Yoga Flow",
  "instructor": "Priya Sharma",
  "class_datetime": "2025-06-09T07:00:00+05:30",
  "client_name": "John Doe",
  "client_email": "john.doe@example.com"
}
```

### 3. Get User Bookings
```http
GET /bookings?email=john.doe@example.com&timezone=Asia/Kolkata
```

**Response:**
```json
[
  {
    "id": 1,
    "class_id": 1,
    "class_name": "Yoga Flow",
    "instructor": "Priya Sharma",
    "class_datetime": "2025-06-09T07:00:00+05:30",
    "client_name": "John Doe",
    "client_email": "john.doe@example.com",
    "booking_time": "2025-06-06T10:30:00+00:00"
  }
]
```

##  Sample cURL Commands

### Get All Classes
```bash
curl -X GET "http://localhost:8000/classes" \
  -H "accept: application/json"
```

### Get Classes in Different Timezone
```bash
curl -X GET "http://localhost:8000/classes?timezone=UTC" \
  -H "accept: application/json"
```

### Book a Class
```bash
curl -X POST "http://localhost:8000/book" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": 1,
    "client_name": "John Doe",
    "client_email": "john.doe@example.com"
  }'
```

### Get User Bookings
```bash
curl -X GET "http://localhost:8000/bookings?email=john.doe@example.com" \
  -H "accept: application/json"
```

## Testing

Run the unit tests:

```bash
# Run all tests
pytest test_main.py -v

# Run tests with coverage
pytest test_main.py -v --cov=main

# Run specific test
pytest test_main.py::test_book_class_success -v
```

## Timezone Handling

The API stores all class times in IST (Indian Standard Time) and converts them to the requested timezone:

- **Default timezone**: `Asia/Kolkata` (IST)
- **Supported timezones**: Any valid timezone (e.g., `UTC`, `US/Eastern`, `Europe/London`)
- **Conversion**: Automatic conversion when fetching classes or bookings

Example timezone conversions:
```bash
# Get classes in UTC
curl "http://localhost:8000/classes?timezone=UTC"

# Get classes in US Eastern Time
curl "http://localhost:8000/classes?timezone=US/Eastern"
```

## Error Handling

The API handles various error scenarios:

- **404**: Class not found or already occurred
- **400**: No available slots, duplicate booking
- **422**: Invalid input data (validation errors)
- **500**: Internal server errors

## Sample Data

The API comes with pre-loaded sample classes:

1. **Yoga Flow** - Priya Sharma (Mon 7:00 AM IST)
2. **Zumba Dance** - Rahul Kumar (Mon 6:30 PM IST)
3. **HIIT Training** - Anjali Singh (Tue 6:30 AM IST)
4. **Power Yoga** - Priya Sharma (Tue 7:00 PM IST)
5. **Cardio Blast** - Vikram Patel (Wed 7:30 AM IST)

## Security Considerations

- Input validation using Pydantic models
- SQL injection prevention through parameterized queries
- Email validation for all booking requests
- Proper error handling without exposing sensitive information

## Deployment

For production deployment:

1. Use environment variables for configuration
2. Implement proper database connection pooling
3. Add authentication and authorization
4. Use HTTPS
5. Add rate limiting
6. Implement proper logging and monitoring

## Development Notes

- **Database**: SQLite for simplicity, easily replaceable with PostgreSQL/MySQL
- **Timezone**: All internal storage in IST, conversion on demand
- **Validation**: Comprehensive input validation using Pydantic
- **Testing**: Unit tests cover all major functionality
- **Documentation**: Automatic API documentation with FastAPI

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests to ensure everything works
6. Submit a pull request

## License

This project is created for educational purposes and is free to use and modify.

---

**Happy Coding!**
