## Project Overview

AI Travel Agent - A LangChain/LangGraph-based agent that helps users find flights and hotels using SearchAPI.io (Google Flights & Hotels).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Architecture

```
app.py (Streamlit UI)
└── agent/
    ├── main.py          # Agent creation with LangGraph InMemorySaver
    ├── tools.py         # LangChain tools (flight_search, hotel_search)
    ├── llm_provider.py  # OpenAI LLM configuration
    ├── system_prompt.py # System prompt with current date
    └── dependencies.py  # Pydantic settings from .env
└── services/
    ├── flight_search.py # FlightSearcher class for SearchAPI.io
    └── hotel_search.py  # HotelSearcher class for SearchAPI.io
```

### Key Components

- **agent/main.py**: Creates agent using `create_agent` from LangChain with `InMemorySaver` for conversation memory. Exports `create_travel_agent()` and `run_agent(user_input, thread_id)`.
- **agent/tools.py**: LangChain tools with Pydantic input schemas. Uses services for search.
- **services/flight_search.py**: `FlightSearcher` class with `search()` for one-way and `search_roundtrip()` for round trips. Returns `FlightSearchResult` with `request_url`.
- **services/hotel_search.py**: `HotelSearcher` class with `search()` for hotel lookups. Returns `HotelSearchResult` with `request_url`.

## Configuration

Create a `.env` file:
```
OPENAI_API_KEY=your_openai_key
SEARCHAPI_API_KEY=your_searchapi_key
```

## Usage

```python
from agent.main import run_agent

# run_agent uses thread_id for conversation memory
response = run_agent("Find flights from NYC to Paris on 2025-03-15", thread_id="1")
```
