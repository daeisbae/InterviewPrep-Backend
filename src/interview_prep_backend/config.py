from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = Field(default="development", alias="ENVIRONMENT")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    aws_region: Optional[str] = Field(default=None, alias="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket: Optional[str] = Field(default=None, alias="AWS_S3_BUCKET")
    coaching_rules_path: str = Field(default="data/rules.json", alias="COACHING_RULES_PATH")
    filler_words: List[str] = Field(
        default_factory=lambda: [
            "um",
            "uh",
            "like",
            "you know",
            "actually",
            "basically",
            "literally",
        ]
    )
    low_confidence_threshold: float = Field(default=0.45, alias="LOW_CONFIDENCE_THRESHOLD")
    high_anxiety_threshold: float = Field(default=0.6, alias="HIGH_ANXIETY_THRESHOLD")
    enable_external_apis: bool = Field(default=False, alias="ENABLE_EXTERNAL_APIS")

    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
