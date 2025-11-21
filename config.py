from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API Configuration settings"""

    # API Security
    api_key: str = ""

    # Environment
    environment: str = Field(default="dev", alias="ENV")

    # Go executable configuration
    prod_executable_path: str = "/app/infinitools"
    prod_executable_name: str = "infinitools"
    dev_go_project_path: str = Field(default="../infinitools", alias="GO_PROJECT_PATH")

    # Default values
    default_git_user: str = "github-actions"
    default_motive: str = "Automated deployment"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True


settings = Settings()

# Validate required settings
if not settings.api_key:
    raise ValueError("API_KEY must be set in environment variables or .env file")
