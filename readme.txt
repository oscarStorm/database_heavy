Database-Heavy Booking System
A booking system architecture experiment that puts most business-rule enforcement in MySQL rather than the Python application.

This repository is a companion to backend_heavy. Both projects implement the same core use cases, allowing the two approaches to be compared directly.
Features
- Create and list customers
- Create and list bookable resources (such as tables)
- Create and list bookings
- Find resources available during a requested time period
- Cancel bookings
Tech Stack
- Python and FastAPI — HTTP API
- Pydantic — request-shape validation
- MySQL 8.4 — data storage and business-rule enforcement
- Stored procedures, triggers and constraints — database-side logic
- PyMySQL — direct database access, without an ORM
- Textual — terminal-based user interface
- HTTPX — API requests from the terminal client
- Docker Compose — local MySQL instance
Architecture
Textual terminal UI
        |
       HTTPX
        |
FastAPI (main.py)
        |
Pydantic (schemas.py)
        |
repositories.py
        |
MySQL stored procedures
        |
Triggers / constraints
        |
    MySQL tables
The API handles HTTP requests, validates their structure and calls repository functions. The repository layer delegates operations to MySQL stored procedures, where most of the actual business rules are enforced.

This is the main contrast with backend_heavy, where the Python backend takes primary responsibility for those decisions.
Business Rules
The database-heavy implementation enforces the following rules in MySQL:
Area	Rule
Customers	Names must contain at least two characters
Customers	Email addresses must end in example.com
Resources	Names cannot be blank
Resources	Capacity must be at least 1
Bookings	start_time must be earlier than end_time
Bookings	Bookings for the same resource must not overlap
Bookings	Inactive resources cannot be booked


The example.com email restriction is a deliberately narrow validation rule for this experiment, not a general-purpose production email policy.
Project Structure
app/                 API, validation, repository and client code
scripts/             Project scripts
sql/                 Database schema and SQL logic
tests/               Test code
docker-compose.yml   MySQL development container
requirements.txt     Python dependencies
Getting Started
Requirements: Python, Docker and Docker Compose.
1. Clone the repository and install dependencies:
   git clone https://github.com/oscarStorm/database_heavy.git
   cd database_heavy
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
2. Create a .env file at the repository root:
   MYSQL_ROOT_PASSWORD=change-me-root
   MYSQL_DATABASE=booking_db
   MYSQL_USER=booking_user
   MYSQL_PASSWORD=change-me
   These are example local-development credentials. Configure any additional database connection variables required by the Python application.
3. Start MySQL:
   docker compose up -d
   The database is exposed on localhost:3307, mapped to port 3306 inside its container. This lets it run alongside backend_heavy, whose Compose setup uses host port 3306. The Compose file starts only MySQL.
4. Initialize the schema, stored procedures, triggers and constraints using the files in sql/ and any setup scripts in scripts/. Then start the FastAPI application and terminal client from app/.
   Note: The exact initialization and application launch commands have not been verified here; check the corresponding entry points before running them.
Why Put Logic in the Database?
Database-side validation centralizes rules close to the data. This is useful when multiple clients or services access the same database and should follow the same restrictions.

The trade-off is that more application behavior becomes coupled to MySQL-specific features. It can also be harder to inspect, version, and test logic spread across stored procedures, triggers and constraints.

This repository is an experiment in those trade-offs, not a claim that database-heavy design is always preferable.
Related Project
backend_heavy — the equivalent booking system with business logic primarily implemented in the Python backend.
