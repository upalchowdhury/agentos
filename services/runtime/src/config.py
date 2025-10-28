import logging
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Service
    SERVICE_NAME: str = Field(default="runtime-service")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=False)
    
    # Database
    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="agentos")
    POSTGRES_USER: str = Field(default="agentos")
    POSTGRES_PASSWORD: str = Field(default="changeme")
    
    # Redis
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: str = Field(default="6379")
    REDIS_DB: int = Field(default=0)
    
    # Docker
    DOCKER_HOST: str = Field(default="unix:///var/run/docker.sock")
    DOCKER_NETWORK: str = Field(default="agentos-network")
    
    # Agent Execution
    DEFAULT_MEMORY_LIMIT: str = Field(default="512m")
    DEFAULT_CPU_LIMIT: str = Field(default="0.5")
    MAX_EXECUTION_TIME: int = Field(default=30)
    
    # Services
    IDENTITY_SERVICE_URL: str = Field(default="http://identity:3000")
    GATEWAY_SERVICE_URL: str = Field(default="http://gateway:8080")
    OPA_URL: Optional[str] = Field(default=None)
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        redis_port = self.REDIS_PORT
        if isinstance(redis_port, str) and redis_port.startswith("tcp://"):
            redis_port = redis_port.split(":")[-1]
        return f"redis://{self.REDIS_HOST}:{redis_port}/{self.REDIS_DB}"


settings = Settings()

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
