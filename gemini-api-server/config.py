"""
Configuration management for Gemini API Server.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1


class GeminiConfig(BaseModel):
    """Gemini API configuration."""
    secure_1psid: Optional[str] = None
    secure_1psidts: Optional[str] = None
    proxy: Optional[str] = None
    use_browser_cookies: bool = False


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"


class Settings(BaseModel):
    """Main settings class."""
    server: ServerConfig = Field(default_factory=ServerConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_settings() -> Settings:
    """
    Load settings from environment variables and .env file.
    """
    # Load .env file if it exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Create settings from environment variables
    server_config = ServerConfig(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        workers=int(os.getenv("WORKERS", 1))
    )
    
    gemini_config = GeminiConfig(
        secure_1psid=os.getenv("SECURE_1PSID"),
        secure_1psidts=os.getenv("SECURE_1PSIDTS"),
        proxy=os.getenv("PROXY"),
        use_browser_cookies=os.getenv("USE_BROWSER_COOKIES", "false").lower() == "true"
    )
    
    logging_config = LoggingConfig(
        level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    return Settings(
        server=server_config,
        gemini=gemini_config,
        logging=logging_config
    )


# Global settings instance
settings = load_settings()
