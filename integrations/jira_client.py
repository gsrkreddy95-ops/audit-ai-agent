"""
Jira Search Client
===================

Provides reliable, paginated Jira search without artificial 1000-result limits.
Handles complex JQL filters, rate limiting, and returns all matching issues by
paging until the server-reported total is reached or an optional hard limit is
met.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Generator, Iterable, List, Optional, Set

import requests
from requests import Response
from requests.auth import HTTPBasicAuth
from rich.console import Console

console = Console()


@dataclass
class JiraIssue:
    """Lightweight Jira issue record returned by :class:`JiraSearchClient`."""

    key: str
    fields: Dict


class JiraSearchError(Exception):
    """Raised when Jira search fails after retries."""


class JiraSearchClient:
    """Small helper that retrieves Jira search results without a 1000-item cap.

    The client automatically paginates with the maximum allowed page size and
    gracefully handles rate limiting or transient errors with bounded retries.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        api_version: str = "3",
        timeout: int = 30,
        page_size: int = 100,
        max_retries: int = 3,
    ):
        self.base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
        self.email = email or os.getenv("JIRA_EMAIL")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")
        self.api_version = api_version
        self.timeout = timeout
        self.page_size = min(page_size, 100)  # Jira caps at 100 per request
        self.max_retries = max_retries

        if not self.base_url or not self.email or not self.api_token:
            raise ValueError(
                "JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be configured"
            )

        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.email, self.api_token)
        self.session.headers.update({"Accept": "application/json"})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def search(
        self,
        jql: str,
        fields: Optional[Iterable[str]] = None,
        limit: Optional[int] = None,
        expand: Optional[Iterable[str]] = None,
        enforce_filters: Optional[Dict] = None,
    ) -> List[JiraIssue]:
        """Return all issues that match *jql*, honoring an optional hard *limit*.

        The method paginates through the entire result set instead of stopping
        at 1000 issues, ensuring complete coverage for complex filters.
        """

        return list(
            self.iter_issues(
                jql=jql,
                fields=fields,
                limit=limit,
                expand=expand,
                enforce_filters=enforce_filters,
            )
        )

    def iter_issues(
        self,
        jql: str,
        fields: Optional[Iterable[str]] = None,
        limit: Optional[int] = None,
        expand: Optional[Iterable[str]] = None,
        enforce_filters: Optional[Dict] = None,
    ) -> Generator[JiraIssue, None, None]:
        """Yield issues that match *jql* with robust pagination.

        Args:
            jql: Jira Query Language string.
            fields: Optional iterable of field names to include.
            limit: Optional maximum number of issues to return.
            expand: Optional expand parameters.
            enforce_filters: Optional dict to apply local validation when Jira
                misreports totals or omits filter enforcement. Supported keys:
                ``labels`` (str or list[str]), ``created_from`` and
                ``created_to`` (datetime/date/ISO string).
        """

        start_at = 0
        fetched = 0
        total: Optional[int] = None
        seen_keys: Set[str] = set()
        matches_filter: Callable[[Dict], bool] = self._build_filter(enforce_filters)

        while True:
            max_results = self._page_size_for_limit(limit, fetched)
            response = self._request(
                "GET",
                f"{self.base_url}/rest/api/{self.api_version}/search",
                params={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": max_results,
                    "fields": ",".join(fields) if fields else None,
                    "expand": ",".join(expand) if expand else None,
                },
            )

            data = response.json()
            issues = data.get("issues", [])
            total = data.get("total", total)

            if not issues:
                break

            new_keys_found = False

            for issue in issues:
                issue_key = issue.get("key")
                if issue_key in seen_keys:
                    continue

                seen_keys.add(issue_key)
                new_keys_found = True

                fields = issue.get("fields", {})
                if not matches_filter(fields):
                    continue

                yield JiraIssue(key=issue_key, fields=fields)
                fetched += 1
                if limit and fetched >= limit:
                    return

            start_at += len(issues)
            if not new_keys_found:
                console.print(
                    "[yellow]⚠️  Jira pagination returned duplicate pages; stopping to avoid infinite loop.[/yellow]"
                )
                break

            if total is not None and start_at >= total:
                break

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _page_size_for_limit(self, limit: Optional[int], fetched: int) -> int:
        if limit is None:
            return self.page_size
        remaining = max(limit - fetched, 0)
        return min(self.page_size, remaining or self.page_size)

    def _build_filter(self, enforce_filters: Optional[Dict]) -> Callable[[Dict], bool]:
        if not enforce_filters:
            return lambda _: True

        labels_filter = enforce_filters.get("labels")
        if labels_filter and isinstance(labels_filter, str):
            labels_filter = [labels_filter]

        created_from = self._normalize_datetime(enforce_filters.get("created_from"))
        created_to = self._normalize_datetime(enforce_filters.get("created_to"))

        def _matches(fields: Dict) -> bool:
            if labels_filter:
                issue_labels = set(fields.get("labels") or [])
                if not set(labels_filter).issubset(issue_labels):
                    return False

            created_raw = fields.get("created")
            if created_raw and (created_from or created_to):
                created_dt = self._parse_created(created_raw)
                if created_from and created_dt < created_from:
                    return False
                if created_to and created_dt > created_to:
                    return False

            return True

        return _matches

    def _normalize_datetime(self, value: Optional[object]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            # Support date objects or strings in YYYY-MM-DD form
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            parsed = datetime.fromisoformat(str(value))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            console.print(
                f"[yellow]⚠️  Unable to parse created date '{value}', skipping date filter.[/yellow]"
            )
            return None

    def _parse_created(self, value: str) -> datetime:
        # Jira returns offsets like -0700; ensure compatibility with fromisoformat
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        if len(value) >= 5 and value[-3] != ":" and value[-5] in {"+", "-"}:
            value = f"{value[:-2]}:{value[-2:]}"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def _request(self, method: str, url: str, params: Optional[Dict] = None) -> Response:
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    params={k: v for k, v in (params or {}).items() if v is not None},
                    timeout=self.timeout,
                )

                if response.status_code == 429:
                    self._sleep_with_backoff(attempt, reason="rate limited (429)")
                    continue

                if 500 <= response.status_code < 600:
                    self._sleep_with_backoff(attempt, reason=f"server error {response.status_code}")
                    continue

                response.raise_for_status()
                return response

            except Exception as exc:  # Broad on purpose to retry any transient failure
                last_error = exc
                self._sleep_with_backoff(attempt, reason=str(exc))

        raise JiraSearchError(f"Jira request failed after {self.max_retries} retries: {last_error}")

    def _sleep_with_backoff(self, attempt: int, reason: str) -> None:
        delay = min(2 ** attempt, 10)
        console.print(f"[yellow]⚠️  Jira request retry {attempt}/{self.max_retries} ({reason}); sleeping {delay}s[/yellow]")
        time.sleep(delay)


__all__ = ["JiraSearchClient", "JiraIssue", "JiraSearchError"]
