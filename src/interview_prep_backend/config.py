from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    environment: str = Field(default="development", alias="ENVIRONMENT")
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
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

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings()  # type: ignore[arg-type]
