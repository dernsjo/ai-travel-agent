import httpx
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Optional

from services.flight_search import FlightSearcher, format_flight_result
from services.hotel_search import HotelSearcher, format_hotel_result


class FlightSearchInput(BaseModel):
    origin: str = Field(description="Departure airport code (e.g., 'JFK', 'LAX')")
    destination: str = Field(description="Arrival airport code (e.g., 'CDG', 'LHR')")
    departure_date: str = Field(description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(default=None, description="Return date in YYYY-MM-DD format for round trips")


class HotelSearchInput(BaseModel):
    location: str = Field(description="City or location to search for hotels")
    check_in: str = Field(description="Check-in date in YYYY-MM-DD format")
    check_out: str = Field(description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(default=2, description="Number of guests")


@tool(args_schema=FlightSearchInput)
def flight_search(origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> str:
    """Search for flights between two airports on specified dates."""
    try:
        searcher = FlightSearcher()
        if return_date:
            result = searcher.search_roundtrip(origin, destination, departure_date, return_date)
        else:
            result = searcher.search(origin, destination, departure_date)
        return format_flight_result(result)
    except httpx.HTTPError as e:
        return f"Error searching flights: {str(e)}"


@tool(args_schema=HotelSearchInput)
def hotel_search(location: str, check_in: str, check_out: str, guests: int = 2) -> str:
    """Search for hotels in a location for specified dates."""
    try:
        searcher = HotelSearcher()
        result = searcher.search(location, check_in, check_out, guests)
        return format_hotel_result(result)
    except httpx.HTTPError as e:
        return f"Error searching hotels: {str(e)}"
