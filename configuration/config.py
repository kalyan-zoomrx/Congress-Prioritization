from dataclasses import dataclass

@dataclass
class LitellmConfig:
    model: str = "gpt-4.1"