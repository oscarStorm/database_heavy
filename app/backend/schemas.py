from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomerCreate(BaseModel):
    name: str
    email: str


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str


class RestaurantTableCreate(BaseModel):
    capacity: int
    tablename: str
    active: bool = True


class RestaurantTableResponse(BaseModel):
    id: int
    capacity: int
    tablename: str
    active: bool


class Booking(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    customer_id: int
    resource_id: int
    start_time: datetime
    end_time: datetime


class BookingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    customer_id: int
    resource_id: int
    start_time: datetime
    end_time: datetime
