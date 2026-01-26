from pydantic_settings import BaseSettings


class DBConfig(BaseSettings):
    postgres_user: str
    postgres_db: str
    postgres_password: str
    postgres_host: str

    @property
    def conn_url(self):
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:5432/{self.postgres_db}"

    @property
    def formatted_conn_url(self):
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:5432/{self.postgres_db}"


class AppConfig(BaseSettings):
    token_expire_time: int
    secret: str
