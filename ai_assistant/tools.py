import json
from random import randint
from datetime import date, datetime
from llama_index.core.tools import QueryEngineTool, FunctionTool, ToolMetadata
from ai_assistant.rags import TravelGuideRAG
from ai_assistant.prompts import travel_guide_qa_tpl, travel_guide_description
from ai_assistant.config import get_agent_settings
from ai_assistant.models import (
    TripReservation,
    TripType,
    HotelReservation,
    RestaurantReservation,
    TripSummary,
    Activity,
)
from ai_assistant.utils import save_reservation

SETTINGS = get_agent_settings()

travel_guide_tool = QueryEngineTool(
    query_engine=TravelGuideRAG(
        store_path=SETTINGS.travel_guide_store_path,
        data_dir=SETTINGS.travel_guide_data_path,
        qa_prompt_tpl=travel_guide_qa_tpl,
    ).get_query_engine(),
    metadata=ToolMetadata(
        name="travel_guide", description=travel_guide_description, return_direct=False
    ),
)


# Tool functions
def reserve_flight(date_str: str, departure: str, destination: str) -> TripReservation:
    """
    Reserves a flight given the departure and destination locations and a date in ISO format (YYYY-MM-DD).

    Parameters:
    - date_str: The date of the flight in ISO format.
    - departure: The departure location (city, airport code, etc.).
    - destination: The destination location (city, airport code, etc.).

    Returns:
    - A TripReservation object with the details of the flight reservation.
    """
    print(
        f"Making flight reservation from {departure} to {destination} on date: {date}"
    )
    reservation = TripReservation(
        trip_type=TripType.flight,
        departure=departure,
        destination=destination,
        date=date.fromisoformat(date_str),
        cost=randint(200, 700),
    )

    save_reservation(reservation)
    return reservation


flight_tool = FunctionTool.from_defaults(fn=reserve_flight, return_direct=False)


def reserve_bus(date_str: str, departure: str, destination: str) -> TripReservation:
    """
    Reserves a bus ticket given the departure and destination locations and a date in ISO format (YYYY-MM-DD).

    Parameters:
    - date_str: The date of the bus trip in ISO format.
    - departure: The departure location.
    - destination: The destination location.

    Returns:
    - A TripReservation object with the details of the bus reservation.
    """
    print(
        f"Making bus reservation from {departure} to {destination} on date: {date_str}"
    )
    reservation = TripReservation(
        trip_type=TripType.bus,
        departure=departure,
        destination=destination,
        date=date.fromisoformat(date_str),
        cost=randint(50, 200),
    )

    save_reservation(reservation)
    return reservation


bus_tool = FunctionTool.from_defaults(fn=reserve_bus, return_direct=False)


def reserve_hotel(
    checkin_date_str: str, checkout_date_str: str, hotel_name: str, city: str
) -> HotelReservation:
    """
    Reserves a hotel room given the check-in and check-out dates, hotel name, and city.

    Parameters:
    - checkin_date_str: The check-in date in ISO format (YYYY-MM-DD).
    - checkout_date_str: The check-out date in ISO format (YYYY-MM-DD).
    - hotel_name: The name of the hotel.
    - city: The city where the hotel is located.

    Returns:
    - A HotelReservation object with the details of the reservation.
    """
    print(
        f"Making hotel reservation at {hotel_name} in {city} from {checkin_date_str} to {checkout_date_str}"
    )
    reservation = HotelReservation(
        checkin_date=date.fromisoformat(checkin_date_str),
        checkout_date=date.fromisoformat(checkout_date_str),
        hotel_name=hotel_name,
        city=city,
        cost=randint(100, 1000),
    )

    save_reservation(reservation)
    return reservation


hotel_tool = FunctionTool.from_defaults(fn=reserve_hotel, return_direct=False)


def reserve_restaurant(
    reservation_datetime_str: str,
    restaurant: str,
    city: str,
    dish: str = "Not specified",
) -> RestaurantReservation:
    """
    Reserves a table at a restaurant given the reservation datetime, restaurant name, city, and dish preference.

    Parameters:
    - reservation_datetime_str: The reservation datetime in ISO format (YYYY-MM-DDTHH:MM:SS).
    - restaurant: The name of the restaurant.
    - city: The city where the restaurant is located.
    - dish: The preferred dish.

    Returns:
    - A RestaurantReservation object with the details of the reservation.
    """
    reservation_datetime = datetime.fromisoformat(reservation_datetime_str)
    print(
        f"Making restaurant reservation at {restaurant} in {city} on {reservation_datetime} with preferred dish: {dish}"
    )
    reservation = RestaurantReservation(
        reservation_time=reservation_datetime,
        restaurant=restaurant,
        city=city,
        dish=dish,
        cost=randint(20, 100),
    )

    save_reservation(reservation)
    return reservation


restaurant_tool = FunctionTool.from_defaults(fn=reserve_restaurant, return_direct=False)


def trip_summary(file_path: str = "trip.json") -> TripSummary:
    """
    Summarizes the content of the log file, organizing saved activities by place and date,
    calculating the total budget, and providing comments on each place and activity.

    Parameters:
    - file_path: Path to the trip.json file containing trip activities and details. There is a path by default.

    Returns:
    - A TripSummary object with organized activities, total budget, and comments.
    """
    try:
        with open(file_path, "r") as file:
            trip_data = json.load(file)

        total_budget = 0.0
        activities_by_place = {}

        # Process each reservation and organize data
        for item in trip_data:
            reservation_type = item.get("reservation_type")
            if reservation_type == "TripReservation":
                place = f"{item['departure']} to {item['destination']}"
                activity_date = item["date"]
                description = (
                    f"Flight from {item['departure']} to {item['destination']}"
                )
            elif reservation_type == "HotelReservation":
                place = item["city"]
                activity_date = item["checkin_date"]
                description = f"Hotel stay at {item['hotel_name']} from {item['checkin_date']} to {item['checkout_date']}"
            elif reservation_type == "RestaurantReservation":
                place = item["city"]
                activity_date = item["reservation_time"]
                description = f"Restaurant reservation at {item['restaurant']} at {item['reservation_time']}"
            else:
                continue

            cost = float(item["cost"])
            total_budget += cost

            if place not in activities_by_place:
                activities_by_place[place] = []

            activities_by_place[place].append(
                {
                    "date": activity_date,
                    "description": description,
                    "cost": f"${cost:.2f}",
                }
            )

        # Convert activities into a prompt-friendly format for the agent
        activities_text = ""
        for place, activities in activities_by_place.items():
            activities_text += f"Place: {place}\n"
            for activity in activities:
                activities_text += (
                    f"  Date: {activity['date']}, "
                    f"Description: {activity['description']}, "
                    f"Cost: {activity['cost']}.\n"
                )

        # Generate summary
        summary = f"Total budget: ${total_budget:.2f}. The trip includes activities in the following places: "
        summary += ", ".join(activities_by_place.keys()) + "."

        return TripSummary(
            total_budget=total_budget,
            activities_by_place=activities_by_place,
            summary=summary,
        )

    except FileNotFoundError:
        raise Exception("Trip log file not found")
    except json.JSONDecodeError:
        raise Exception(
            "Error decoding the trip log file. Ensure it is in the correct JSON format."
        )
    except Exception as e:
        raise Exception(f"An error occurred while summarizing the trip: {str(e)}")


trip_summary_tool = FunctionTool.from_defaults(fn=trip_summary, return_direct=False)
