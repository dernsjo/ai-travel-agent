import httpx
from dataclasses import dataclass, field
from typing import Optional

from agent.dependencies import settings


@dataclass
class FlightSegment:
    departure_airport: str
    departure_id: str
    departure_time: str
    arrival_airport: str
    arrival_id: str
    arrival_time: str
    airline: str
    flight_number: str
    duration_min: int
    airplane: Optional[str] = None


@dataclass
class Layover:
    airport: str
    duration_min: int


@dataclass
class Flight:
    price: int
    segments: list[FlightSegment]
    layovers: list[Layover]
    total_duration_min: int
    stops: int


@dataclass
class FlightSearchResult:
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str]
    outbound_flights: list[Flight]
    return_flights: list[Flight]
    request_url: str


class FlightSearcher:
    """Generic flight search using SearchAPI.io Google Flights engine."""

    def __init__(
        self,
        currency: str = "USD",
        travel_class: str = "economy",
        adults: int = 1,
    ):
        self.currency = currency
        self.travel_class = travel_class
        self.adults = adults

    def _parse_flight(self, flight_data: dict) -> Flight:
        """Parse a flight from API response."""
        segments = []
        for f in flight_data.get("flights", []):
            segments.append(FlightSegment(
                departure_airport=f["departure_airport"]["name"],
                departure_id=f["departure_airport"]["id"],
                departure_time=f"{f['departure_airport']['date']} {f['departure_airport']['time']}",
                arrival_airport=f["arrival_airport"]["name"],
                arrival_id=f["arrival_airport"]["id"],
                arrival_time=f"{f['arrival_airport']['date']} {f['arrival_airport']['time']}",
                airline=f["airline"],
                flight_number=f["flight_number"],
                duration_min=f["duration"],
                airplane=f.get("airplane"),
            ))

        layovers = [
            Layover(airport=lay["name"], duration_min=lay["duration"])
            for lay in flight_data.get("layovers", [])
        ]

        return Flight(
            price=flight_data.get("price", 0),
            segments=segments,
            layovers=layovers,
            total_duration_min=flight_data.get("total_duration", 0),
            stops=len(segments) - 1 if segments else 0,
        )

    def search(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        max_results: int = 5,
    ) -> FlightSearchResult:
        """Search for flights between two airports."""
        params = {
            "engine": "google_flights",
            "api_key": settings.searchapi_api_key,
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date,
            "adults": str(self.adults),
            "travel_class": self.travel_class,
            "currency": self.currency,
            "hl": "en",
            "gl": "us",
        }

        if return_date:
            params["return_date"] = return_date
            params["flight_type"] = "round_trip"
        else:
            params["flight_type"] = "one_way"

        response = httpx.get(settings.searchapi_base_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        request_url = data.get("search_metadata", {}).get("request_url", "")

        # Parse outbound flights
        raw_flights = data.get("best_flights", []) + data.get("other_flights", [])
        outbound_flights = [self._parse_flight(f) for f in raw_flights[:max_results]]

        # For round trips, we'd need to make a second call with departure_token
        # to get return flights. For now, return empty list for returns.
        return_flights: list[Flight] = []

        return FlightSearchResult(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=departure_date,
            return_date=return_date,
            outbound_flights=outbound_flights,
            return_flights=return_flights,
            request_url=request_url,
        )

    def search_roundtrip(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        max_results: int = 5,
    ) -> FlightSearchResult:
        """Search for round trip flights with return options."""
        # First search to get outbound options
        result = self.search(origin, destination, departure_date, return_date, max_results)

        if not result.outbound_flights:
            return result

        # Get departure token from first outbound flight to search returns
        params = {
            "engine": "google_flights",
            "api_key": settings.searchapi_api_key,
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date,
            "return_date": return_date,
            "flight_type": "round_trip",
            "currency": self.currency,
            "hl": "en",
            "gl": "us",
        }

        response = httpx.get(settings.searchapi_base_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Get first flight's departure token
        all_flights = data.get("best_flights", []) + data.get("other_flights", [])
        if all_flights and "departure_token" in all_flights[0]:
            token = all_flights[0]["departure_token"]

            # Search for return flights
            params["departure_token"] = token
            return_response = httpx.get(settings.searchapi_base_url, params=params, timeout=60)
            return_response.raise_for_status()
            return_data = return_response.json()

            raw_returns = return_data.get("best_flights", []) + return_data.get("other_flights", [])
            result.return_flights = [self._parse_flight(f) for f in raw_returns[:max_results]]
            result.request_url = return_data.get("search_metadata", {}).get("request_url", result.request_url)

        return result


def format_flight_result(result: FlightSearchResult) -> str:
    """Format flight search result for display."""
    lines = []

    if result.return_date:
        lines.append(f"Flights: {result.origin} → {result.destination}")
        lines.append(f"{result.departure_date} - {result.return_date}")
    else:
        lines.append(f"One-way: {result.origin} → {result.destination}")
        lines.append(f"{result.departure_date}")

    lines.append("")

    if not result.outbound_flights:
        lines.append("No flights found.")
    else:
        lines.append("**Outbound options:**")
        for i, flight in enumerate(result.outbound_flights, 1):
            stops = "Direct" if flight.stops == 0 else f"{flight.stops} stop{'s' if flight.stops > 1 else ''}"
            hours, mins = divmod(flight.total_duration_min, 60)
            duration = f"{hours}h {mins}m"
            airline = flight.segments[0].airline if flight.segments else "Unknown"
            lines.append(f"{i}. {airline} - ${flight.price} ({stops}, {duration})")

    if result.return_flights:
        lines.append("")
        lines.append("**Return options:**")
        for i, flight in enumerate(result.return_flights, 1):
            stops = "Direct" if flight.stops == 0 else f"{flight.stops} stop{'s' if flight.stops > 1 else ''}"
            hours, mins = divmod(flight.total_duration_min, 60)
            duration = f"{hours}h {mins}m"
            airline = flight.segments[0].airline if flight.segments else "Unknown"
            lines.append(f"{i}. {airline} - ${flight.price} ({stops}, {duration})")

    if result.request_url:
        lines.append("")
        lines.append(f"[View on Google Flights]({result.request_url})")

    return "\n".join(lines)
