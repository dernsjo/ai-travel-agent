from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    searchapi_api_key: str
    searchapi_base_url: str = "https://www.searchapi.io/api/v1/search"

    class Config:
        env_file = ".env"


settings = Settings()
