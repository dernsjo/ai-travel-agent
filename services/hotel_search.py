import httpx
from dataclasses import dataclass
from typing import Optional

from agent.dependencies import settings


@dataclass
class HotelAmenity:
    name: str


@dataclass
class Hotel:
    name: str
    description: Optional[str]
    price_per_night: Optional[str]
    total_price: Optional[str]
    rating: Optional[float]
    reviews_count: Optional[int]
    stars: Optional[int]
    address: Optional[str]
    amenities: list[str]
    thumbnail: Optional[str]


@dataclass
class HotelSearchResult:
    location: str
    check_in: str
    check_out: str
    guests: int
    hotels: list[Hotel]
    request_url: str


class HotelSearcher:
    """Generic hotel search using SearchAPI.io Google Hotels engine."""

    def __init__(
        self,
        currency: str = "USD",
    ):
        self.currency = currency

    def _parse_hotel(self, hotel_data: dict) -> Hotel:
        """Parse a hotel from API response."""
        rate = hotel_data.get("rate_per_night", {})

        return Hotel(
            name=hotel_data.get("name", "Unknown"),
            description=hotel_data.get("description"),
            price_per_night=rate.get("lowest") or rate.get("before_taxes_fees"),
            total_price=hotel_data.get("total_rate", {}).get("lowest"),
            rating=hotel_data.get("overall_rating"),
            reviews_count=hotel_data.get("reviews"),
            stars=hotel_data.get("hotel_class"),
            address=hotel_data.get("location", {}).get("address") if isinstance(hotel_data.get("location"), dict) else None,
            amenities=hotel_data.get("amenities", []),
            thumbnail=hotel_data.get("images", [{}])[0].get("thumbnail") if hotel_data.get("images") else None,
        )

    def search(
        self,
        location: str,
        check_in: str,
        check_out: str,
        guests: int = 2,
        max_results: int = 5,
    ) -> HotelSearchResult:
        """Search for hotels in a location."""
        params = {
            "engine": "google_hotels",
            "api_key": settings.searchapi_api_key,
            "q": location,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "adults": str(guests),
            "currency": self.currency,
            "hl": "en",
            "gl": "us",
        }

        response = httpx.get(settings.searchapi_base_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        request_url = data.get("search_metadata", {}).get("request_url", "")

        raw_hotels = data.get("properties", [])
        hotels = [self._parse_hotel(h) for h in raw_hotels[:max_results]]

        return HotelSearchResult(
            location=location,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            hotels=hotels,
            request_url=request_url,
        )


def format_hotel_result(result: HotelSearchResult) -> str:
    """Format hotel search result for display."""
    lines = []

    lines.append(f"🏨 Hotels in {result.location}")
    lines.append(f"📅 {result.check_in} - {result.check_out} ({result.guests} guests)")
    lines.append("")

    if not result.hotels:
        lines.append("No hotels found.")
    else:
        for i, hotel in enumerate(result.hotels, 1):
            # Build hotel line
            stars = "⭐" * hotel.stars if hotel.stars else ""
            rating = f"Rating: {hotel.rating}" if hotel.rating else ""
            reviews = f"({hotel.reviews_count} reviews)" if hotel.reviews_count else ""
            price = hotel.price_per_night or "Price N/A"

            lines.append(f"**{i}. {hotel.name}** {stars}")

            price_rating = []
            if hotel.price_per_night:
                price_rating.append(f"{price}/night")
            if hotel.total_price:
                price_rating.append(f"Total: {hotel.total_price}")
            if rating:
                price_rating.append(f"{rating} {reviews}".strip())

            if price_rating:
                lines.append("   " + " | ".join(price_rating))

            if hotel.amenities:
                lines.append(f"   Amenities: {', '.join(hotel.amenities[:5])}")

            lines.append("")

    if result.request_url:
        lines.append(f"[View on Google Hotels]({result.request_url})")

    return "\n".join(lines)
