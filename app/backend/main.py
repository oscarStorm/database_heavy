from fastapi import FastAPI, HTTPException

from app.backend.repositories import (
    cancel_booking,
    create_booking,
    create_customer,
    create_restaurant_table,
    list_available_tables,
    list_bookings,
    list_bookings_for_table,
    list_customers,
    list_tables,
)
from app.backend.schemas import (
    Booking,
    BookingResponse,
    CustomerCreate,
    CustomerResponse,
    RestaurantTableCreate,
    RestaurantTableResponse,
)

app = FastAPI()


@app.get("/")
def root():
    return {"status": "database-heavy api running"}


@app.get("/customers", response_model=list[CustomerResponse])
def customers():
    return list_customers()


@app.post("/customers", response_model=CustomerResponse)
def add_customer(customer: CustomerCreate):
    try:
        return create_customer(name=customer.name, email=str(customer.email))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/resources", response_model=list[RestaurantTableResponse])
def tables():
    return list_tables()


@app.get("/resources/available", response_model=list[RestaurantTableResponse])
def available_tables(start_time: str, end_time: str):
    try:
        return list_available_tables(start_time=start_time, end_time=end_time)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/resources/{resource_id}/bookings", response_model=list[BookingResponse])
def table_bookings(resource_id: int):
    try:
        return list_bookings_for_table(resource_id=resource_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/resources", response_model=RestaurantTableResponse)
def add_table(table: RestaurantTableCreate):
    try:
        return create_restaurant_table(
            capacity=table.capacity,
            tablename=table.tablename,
            active=table.active,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/booking", response_model=list[BookingResponse])
def bookings():
    return list_bookings()


@app.post("/booking", response_model=BookingResponse)
def book_table(booking: Booking):
    try:
        return create_booking(
            customer_id=booking.customer_id,
            resource_id=booking.resource_id,
            start_time=booking.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=booking.end_time.strftime("%Y-%m-%d %H:%M:%S"),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.delete("/booking/{booking_id}", status_code=204)
def delete_booking(booking_id: int):
    try:
        cancel_booking(booking_id=booking_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

