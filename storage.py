"""Persistence backends for the Streamlit team preference app."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote


class LocalStorage:
    """Simple local JSON persistence for development/testing only."""

    def __init__(self, path: str | Path = "data/submissions.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list_submissions(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save_submission(self, submission: dict[str, Any]) -> None:
        rows = self.list_submissions()
        key = submission["identifier"].lower()
        rows = [r for r in rows if r["identifier"].lower() != key]
        rows.append(submission)
        rows.sort(key=lambda r: r["identifier"].lower())
        self.path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


class GitHubStorage:
    """Store one JSON document per participant in a GitHub repository."""

    def __init__(self, token: str, repo: str, branch: str = "main", folder: str = "submissions") -> None:
        import requests

        self.requests = requests
        self.token = token
        self.repo = repo
        self.branch = branch
        self.folder = folder.strip("/")
        self.base = f"https://api.github.com/repos/{repo}/contents"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(self, method: str, url: str, **kwargs):
        response = self.requests.request(method, url, headers=self.headers, timeout=20, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub storage error {response.status_code}: {response.text[:300]}")
        return response

    def list_submissions(self) -> list[dict[str, Any]]:
        url = f"{self.base}/{quote(self.folder)}?ref={quote(self.branch)}"
        response = self.requests.get(url, headers=self.headers, timeout=20)
        if response.status_code == 404:
            return []
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub storage error {response.status_code}: {response.text[:300]}")
        rows: list[dict[str, Any]] = []
        for item in response.json():
            if item.get("type") != "file" or not item.get("name", "").endswith(".json"):
                continue
            data = self._request("GET", item["url"]).json()
            import base64

            payload = base64.b64decode(data["content"]).decode("utf-8")
            rows.append(json.loads(payload))
        return sorted(rows, key=lambda r: r["identifier"].lower())

    def save_submission(self, submission: dict[str, Any]) -> None:
        import base64

        identifier = submission["identifier"].strip().lower()
        safe = "".join(c for c in identifier if c.isalnum() or c in "-_")
        if not safe:
            raise ValueError("Invalid identifier.")
        path = f"{self.folder}/{safe}.json"
        url = f"{self.base}/{quote(path, safe='/')}"

        existing = self.requests.get(
            f"{url}?ref={quote(self.branch)}", headers=self.headers, timeout=20
        )
        body: dict[str, Any] = {
            "message": f"Update team preference for {safe}",
            "content": base64.b64encode(
                json.dumps(submission, ensure_ascii=False, indent=2).encode("utf-8")
            ).decode("ascii"),
            "branch": self.branch,
        }
        if existing.status_code == 200:
            body["sha"] = existing.json()["sha"]
        elif existing.status_code != 404:
            raise RuntimeError(f"GitHub storage error {existing.status_code}: {existing.text[:300]}")

        self._request("PUT", url, json=body)
