from dataclasses import dataclass

@dataclass
class LitellmConfig:
    MAX_RETRIES: int = 3
    DEFAULT_MODEL: str = "gpt-4.1"
    OUTPUT_FOLDER: str = "output"