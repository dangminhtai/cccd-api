from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Settings:
    port: int = 8000
    default_province_version: str = "current_34"
    api_key: str | None = None
    api_key_mode: Literal["simple", "tiered"] = "simple"
    # Email settings (SMTP)
    email_from: str = "noreply@cccd-api.com"
    email_from_name: str = "CCCD API"

    @staticmethod
    def from_env() -> "Settings":
        port_str = os.getenv("PORT", "8000")
        default_province_version = os.getenv("DEFAULT_PROVINCE_VERSION", "current_34")
        api_key = os.getenv("API_KEY") or None
        api_key_mode = os.getenv("API_KEY_MODE", "simple")
        
        if api_key_mode not in ("simple", "tiered"):
            api_key_mode = "simple"

        try:
            port = int(port_str)
        except ValueError:
            port = 8000

        # Email settings
        email_from = os.getenv("EMAIL_FROM", "noreply@cccd-api.com")
        email_from_name = os.getenv("EMAIL_FROM_NAME", "CCCD API")
        
        return Settings(
            port=port,
            default_province_version=default_province_version,
            api_key=api_key,
            api_key_mode=api_key_mode,
            email_from=email_from,
            email_from_name=email_from_name,
        )


