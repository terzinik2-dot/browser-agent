"""
Configuration settings for Browser Agent.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Agent configuration."""

    # OpenAI API
    api_key: str = ""
    model: str = "gpt-4o"
    max_tokens: int = 1024

    # Browser settings
    headless: bool = False
    viewport_width: int = 1280
    viewport_height: int = 800
    slow_mo: int = 100  # ms between actions for visibility

    # Agent settings
    max_steps: int = 50
    wait_timeout: int = 5000  # ms
    screenshot_quality: int = 80

    # Marker settings
    marker_color: str = "red"
    marker_font_size: int = 14
    marker_padding: int = 2

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables.\n"
                "Set it with: set OPENAI_API_KEY=sk-..."
            )
        return cls(api_key=api_key)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get or create global config."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
