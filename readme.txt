database heavy booking system.

flow:
main.py
-> schemas.py validates request shape
-> repositories.py calls stored procedures
-> mysql procedures/triggers/constraints enforce business rules

same use cases as backend_heavy:
- create customers
- create resources/tables
- create bookings
- list bookings/resources/customers
- list available resources
- cancel bookings

business rules are primarily enforced in mysql:
- customer names must be at least 2 characters
- customer emails must end with @example.com
- resource names cannot be blank
- resource capacity must be at least 1
- bookings must have start_time < end_time
- bookings cannot overlap for the same resource
- inactive resources cannot be booked
