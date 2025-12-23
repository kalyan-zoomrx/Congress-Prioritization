import os
import subprocess
import json
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
import time

IST = ZoneInfo("Asia/Kolkata")


def _get_current_spend_curl(base_url: str, api_key: str) -> float:
    """Get LiteLLM spend using curl via subprocess"""
    url = f"{base_url.rstrip('/')}/key/info"
    cmd = [
        "curl",
        "-s",
        "-X", "GET",
        url,
        "-H", f"Authorization: Bearer {api_key}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Curl failed: {result.stderr}")
    
    data = json.loads(result.stdout)
    return float(data["info"]["spend"])


class SpendTracker:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.environ.get("LITELLM_ENDPOINT")
        self.api_key = api_key or os.environ.get("LITELLM_API_KEY")
        self.start_spend: Optional[float] = None
        self.end_spend: Optional[float] = None
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None

    def initiate(self):
        if not self.base_url or not self.api_key:
            raise RuntimeError("Missing LiteLLM credentials")
        self.start_spend = _get_current_spend_curl(self.base_url, self.api_key)
        self.started_at = datetime.now(IST)

    def close(self):
        if self.start_spend is None:
            raise RuntimeError("close() called before initiate()")
        time.sleep(10)
        self.end_spend = _get_current_spend_curl(self.base_url, self.api_key)
        self.ended_at = datetime.now(IST)
        return {
            "spent": self.end_spend - self.start_spend,
            "total_spent": self.end_spend,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_seconds": (self.ended_at - self.started_at).total_seconds()
        }
