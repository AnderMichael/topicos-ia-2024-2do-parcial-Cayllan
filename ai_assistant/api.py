from fastapi import FastAPI, Depends, Query, HTTPException
from llama_index.core.agent import ReActAgent
from ai_assistant.agent import TravelAgent
from ai_assistant.models import AgentAPIResponse, ReservationAPIResponse
from ai_assistant.prompts import agent_prompt_tpl
from ai_assistant.tools import (
    reserve_bus,
    reserve_flight,
    reserve_hotel,
    reserve_restaurant,
)

from datetime import date, time, datetime


def get_agent() -> ReActAgent:
    return TravelAgent(system_prompt=agent_prompt_tpl).get_agent()


app = FastAPI(title="AI Agent")


def reserve_flight_message(date_str: str, departure: str, destination: str) -> str:
    return f"Flight booked from {departure} to {destination} on {date_str}"


def reserve_bus_message(date_str: str, departure: str, destination: str) -> str:
    return f"Bus ticket booked from {departure} to {destination} on {date_str}"

class InvalidDateOrderException(Exception):
    pass

def reserve_hotel_message(
    start_date_str: str, end_date_str: str, hotel: str, city: str
) -> str:
    return f"Hotel room booked at {hotel} in {city} from {start_date_str} to {end_date_str}"


def reserve_restaurant_message(
    reservation_date_str: str, time: str, restaurant: str, city: str
) -> str:
    return (
        f"Table reserved at {restaurant} in {city} on {reservation_date_str} at {time}"
    )


@app.get("/recommendations/cities")
def recommend_cities(
    notes: list[str] = Query(...), agent: ReActAgent = Depends(get_agent)
) -> AgentAPIResponse:
    prompt = f"recommend the best cities in bolivia with the following notes: {notes}"
    return AgentAPIResponse(status="OK", agent_response=str(agent.chat(prompt)))


@app.get("/recommendations/places")
def recommend_places(
    city: str,
    notes: list[str] = Query(default=[]),
    agent: ReActAgent = Depends(get_agent),
) -> AgentAPIResponse:
    prompt = f"Recommend the best places to visit in {city}"
    if notes:
        prompt += f" based on the following notes: {', '.join(notes)}"
    response = agent.chat(prompt)
    return AgentAPIResponse(status="OK", agent_response=str(response))


@app.get("/recommendations/hotels")
def recommend_hotels(
    city: str,
    notes: list[str] = Query(default=[]),
    agent: ReActAgent = Depends(get_agent),
) -> AgentAPIResponse:
    prompt = f"Recommend the best hotels to stay in {city}"
    if notes:
        prompt += f" based on the following notes: {', '.join(notes)}"
    response = agent.chat(prompt)
    return AgentAPIResponse(status="OK", agent_response=str(response))


@app.get("/recommendations/activities")
def recommend_activities(
    city: str,
    notes: list[str] = Query(default=[]),
    agent: ReActAgent = Depends(get_agent),
) -> AgentAPIResponse:
    prompt = f"Recommend the best activities to do in {city}"
    if notes:
        prompt += f" based on the following notes: {', '.join(notes)}"
    response = agent.chat(prompt)
    return AgentAPIResponse(status="OK", agent_response=str(response))


@app.post("/reservations/flight", response_model=ReservationAPIResponse)
def reserve_flight_endpoint(
    origin: str, destination: str, travel_date: date
) -> ReservationAPIResponse:
    try:
        reserve_flight(travel_date.isoformat(), origin, destination)
        return ReservationAPIResponse(
            status="Success",
            message=reserve_flight_message(
                travel_date.isoformat(), origin, destination
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reservations/bus", response_model=ReservationAPIResponse)
def reserve_bus_endpoint(
    origin: str, destination: str, travel_date: date
) -> ReservationAPIResponse:
    try:
        reserve_bus(travel_date.isoformat(), origin, destination)
        return ReservationAPIResponse(
            status="Success",
            message=reserve_bus(travel_date.isoformat(), origin, destination),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reservations/hotel", response_model=ReservationAPIResponse)
def reserve_hotel_endpoint(
    start_date: date, end_date: date, hotel: str, city: str
) -> ReservationAPIResponse:
    try:
        if end_date <= start_date:
            raise InvalidDateOrderException("La fecha de checkout debe ser posterior a la fecha de checkin")
        reserve_hotel(start_date.isoformat(), end_date.isoformat(), hotel, city)
        return ReservationAPIResponse(
            status="Success",
            message=reserve_hotel_message(
                start_date.isoformat(), end_date.isoformat(), hotel, city
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reservations/restaurant", response_model=ReservationAPIResponse)
def reserve_restaurant_endpoint(
    reservation_date: date, time: time, restaurant: str, city: str
) -> ReservationAPIResponse:
    try:
        reserve_restaurant(
            datetime.combine(reservation_date, time).isoformat(), restaurant, city
        )
        return ReservationAPIResponse(
            status="Success",
            message=reserve_restaurant_message(
                reservation_date.isoformat(), time.isoformat(), restaurant, city
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/trip/report")
def generate_trip_report(agent: ReActAgent = Depends(get_agent)) -> AgentAPIResponse:
    try:
        prompt = f"Generate a detailed travel report of my trip"
        response = agent.chat(prompt)
        return AgentAPIResponse(status="OK", agent_response=str(response))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Trip log file not found")
