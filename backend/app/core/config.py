from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE_PATHS = (PROJECT_ROOT / ".env", BACKEND_DIR / ".env")


class Settings(BaseSettings):
    app_name: str = "AquaShield API"
    debug: bool = False

    # Gemma settings
    gemma_provider: str = "ai_studio"
    gemma_model_name: str = "gemma-4-31b-it"
    google_ai_studio_api_key: str = ""

    # Earth Engine settings
    use_mock_gee: bool = Field(
        default=False,
        validation_alias=AliasChoices("USE_MOCK_GEE", "GEE_USE_MOCK"),
    )
    ee_service_account: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GEE_SERVICE_ACCOUNT_EMAIL",
            "EE_SERVICE_ACCOUNT",
            "EE_SERVICE_ACCOUNT_EMAIL",
        ),
    )
    ee_private_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GEE_SERVICE_ACCOUNT_KEY_PATH",
            "EE_PRIVATE_KEY",
            "GEE_PRIVATE_KEY",
        ),
    )
    gee_service_account_json: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GEE_SERVICE_ACCOUNT_JSON",
            "EE_SERVICE_ACCOUNT_JSON",
        ),
    )
    google_application_credentials: str = Field(
        default="",
        validation_alias=AliasChoices("GOOGLE_APPLICATION_CREDENTIALS"),
    )
    gee_project_id: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GEE_PROJECT_ID",
            "EARTHENGINE_PROJECT",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_PROJECT_ID",
        ),
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATHS,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
