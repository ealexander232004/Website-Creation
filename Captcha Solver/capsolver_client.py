"""Small dependency-free CapSolver client.

Keep API keys and solution tokens out of logs and exception messages.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class CapSolverError(RuntimeError):
    """CapSolver failure that does not expose credentials or solution tokens."""


class CapSolverClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.capsolver.com",
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("A CapSolver API key is required")
        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_environment(cls) -> "CapSolverClient":
        return cls(
            os.environ.get("CAPSOLVER_API_KEY", "").strip(),
            os.environ.get("CAPSOLVER_API_URL", "https://api.capsolver.com").strip(),
        )

    @classmethod
    def from_env_file(cls, path: str | Path = "capsolver.env") -> "CapSolverClient":
        values: dict[str, str] = {}
        for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
        return cls(
            values.get("CAPSOLVER_API_KEY", ""),
            values.get("CAPSOLVER_API_URL", "https://api.capsolver.com"),
        )

    def get_balance(self) -> float:
        return float(self._post("getBalance", {}).get("balance", 0.0))

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return self._post("createTask", {"task": task})

    def get_task_result(self, task_id: str) -> dict[str, Any]:
        return self._post("getTaskResult", {"taskId": task_id})

    def solve(
        self,
        task: dict[str, Any],
        *,
        solve_timeout: float = 120.0,
        poll_interval: float = 1.0,
    ) -> dict[str, Any]:
        created = self.create_task(task)
        if created.get("solution"):
            return dict(created["solution"])
        task_id = created.get("taskId")
        if not task_id:
            raise CapSolverError("CapSolver returned no task ID")

        deadline = time.monotonic() + solve_timeout
        while time.monotonic() < deadline:
            result = self.get_task_result(str(task_id))
            if result.get("status") == "ready":
                solution = result.get("solution")
                if not isinstance(solution, dict):
                    raise CapSolverError("CapSolver returned no solution")
                return solution
            if result.get("status") not in (None, "processing", "idle"):
                raise CapSolverError("CapSolver returned an unexpected task status")
            time.sleep(poll_interval)
        raise CapSolverError("CapSolver task timed out")

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"clientKey": self._api_key, **payload}
        request = Request(
            f"{self.base_url}/{endpoint}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise CapSolverError(f"CapSolver {endpoint} request failed") from exc
        if data.get("errorId", 0):
            code = data.get("errorCode") or "UNKNOWN_ERROR"
            description = data.get("errorDescription") or "request rejected"
            raise CapSolverError(f"CapSolver {code}: {description}")
        return data


def recaptcha_v2_task(
    website_url: str,
    website_key: str,
    *,
    proxy: str | None = None,
    enterprise: bool = False,
    invisible: bool = False,
    data_s: str | None = None,
    page_action: str | None = None,
) -> dict[str, Any]:
    task_type = "ReCaptchaV2EnterpriseTask" if enterprise else "ReCaptchaV2Task"
    if not proxy:
        task_type += "ProxyLess"
    task: dict[str, Any] = {
        "type": task_type,
        "websiteURL": website_url,
        "websiteKey": website_key,
        "isInvisible": invisible,
        "isSession": True,
    }
    if proxy:
        task["proxy"] = proxy
    if data_s:
        if enterprise:
            task["enterprisePayload"] = {"s": data_s}
        else:
            task["recaptchaDataSValue"] = data_s
    if page_action:
        task["pageAction"] = page_action
    return task
