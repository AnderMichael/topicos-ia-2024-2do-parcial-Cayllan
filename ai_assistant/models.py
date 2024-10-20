from pydantic import BaseModel, Field
from enum import Enum
from datetime import date, datetime
from typing import List, Dict

class TripType(str, Enum):
    flight = "FLIGHT"
    bus = "BUS"


class TripReservation(BaseModel):
    trip_type: TripType
    date: date
    departure: str
    destination: str
    cost: int


class HotelReservation(BaseModel):
    checkin_date: date
    checkout_date: date
    hotel_name: str
    city: str
    cost: int


class RestaurantReservation(BaseModel):
    reservation_time: datetime
    restaurant: str
    city: str
    dish: str
    cost: int

class AgentAPIResponse(BaseModel):
    status: str
    agent_response: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ReservationAPIResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
class Activity(BaseModel):
    date: datetime
    place: str
    description: str
    cost: float
    comments: str

class TripSummary(BaseModel):
    total_budget: float
    activities_by_place: Dict[str, List[Dict[str, str]]]
    summary: str