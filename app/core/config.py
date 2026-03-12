from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Pet Flow Premium"
    APP_ENV: str = "development"
    SECRET_KEY: str = "troque-essa-chave"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    POSTGRES_DB: str = "petflow"
    POSTGRES_USER: str = "petflow"
    POSTGRES_PASSWORD: str = "petflow"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str = "postgresql+psycopg2://petflow:petflow@db:5432/petflow"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()