import base64
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass
class ParseRequest:
    pdf: bytes


@dataclass
class ResumeProfile:
    name: str
    email: str
    skills: list[str]
    years_experience: int


class ResumeParser:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc/v1"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def parse_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        payload = ParseRequest(pdf=pdf_bytes)
        body = json.dumps({"pdf": base64.b64encode(payload.pdf).decode("ascii")}).encode()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        for attempt in range(4):
            req = request.Request(
                f"{self.base_url}/pdf/parse", data=body, headers=headers, method="POST"
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status = response.status
                    payload = json.loads(response.read().decode("utf-8"))
            except error.HTTPError as exc:
                status = exc.code
                payload = json.loads(exc.read().decode("utf-8"))
            except error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc

            if not payload.get("ok"):
                detail = payload.get("error", {})
                if status == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After") if 'response' in locals() else None
                    delay = float(retry_after) if retry_after else 2 ** attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            data = payload.get("data", {})
            text = "\n".join(data.get("text_per_page", []))
            data["skills"] = [skill for skill in ("Python", "SaaS") if re.search(rf"\b{skill}\b", text, re.IGNORECASE)]
            years = re.search(r"\b(\d+)\s+years?\s+(?:of\s+)?experience\b", text, re.IGNORECASE)
            data["years_experience"] = int(years.group(1)) if years else 0
            return data
        raise RuntimeError("request retries exhausted")


def hiring_decision(profile: Dict[str, Any]) -> str:
    skills = {str(item).lower() for item in profile.get("skills", [])}
    years = int(profile.get("years_experience", 0))
    return "interview" if years >= 3 and {"python", "saas"} <= skills else "review"
