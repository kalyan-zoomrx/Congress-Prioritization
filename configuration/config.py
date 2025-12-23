from dataclasses import dataclass

@dataclass
class LitellmConfig:
    MAX_RETRIES: int = 3
    DEFAULT_MODEL: str = "claude-haiku-4-5"
    OUTPUT_FOLDER: str = "output"
    model: str = "gpt-4.1"