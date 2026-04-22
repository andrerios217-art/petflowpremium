from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "VectorPet"
    APP_TAGLINE: str = "gestão completa para pet shops"
    APP_ENV: str = "development"

    SECRET_KEY: str = "troque-essa-chave"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 180

    POSTGRES_DB: str = "petflow"
    POSTGRES_USER: str = "petflow"
    POSTGRES_PASSWORD: str = "petflow"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+psycopg2://petflow:petflow@db:5432/petflow"

    CATEGORIZACAO_API_PROVIDER: str = ""
    CATEGORIZACAO_API_MODEL: str = ""
    CATEGORIZACAO_API_URL: str = ""
    CATEGORIZACAO_API_TOKEN: str = ""
    CATEGORIZACAO_API_TIMEOUT: int = 20

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()