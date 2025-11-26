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
from typing import Dict, Generator, Iterable, List, Optional

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
    ) -> List[JiraIssue]:
        """Return all issues that match *jql*, honoring an optional hard *limit*.

        The method paginates through the entire result set instead of stopping
        at 1000 issues, ensuring complete coverage for complex filters.
        """

        return list(self.iter_issues(jql=jql, fields=fields, limit=limit, expand=expand))

    def iter_issues(
        self,
        jql: str,
        fields: Optional[Iterable[str]] = None,
        limit: Optional[int] = None,
        expand: Optional[Iterable[str]] = None,
    ) -> Generator[JiraIssue, None, None]:
        """Yield issues that match *jql* with robust pagination using NEW Jira API.
        
        Migration Info:
        - OLD API: GET /rest/api/{version}/search with startAt parameter  
        - NEW API: POST /rest/api/{version}/search/jql with nextPageToken

        Args:
            jql: Jira Query Language string.
            fields: Optional iterable of field names to include.
            limit: Optional maximum number of issues to return.
            expand: Optional expand parameters.
        """

        next_page_token = None
        fetched = 0

        while True:
            max_results = self._page_size_for_limit(limit, fetched)
            
            # Build payload (fields must be array, not comma-separated string)
            payload = {
                "jql": jql,
                "maxResults": max_results,
            }
            
            # Add fields if specified
            if fields:
                payload["fields"] = list(fields)  # Array, not string
            
            # Add expand if specified  
            if expand:
                payload["expand"] = ",".join(expand)
            
            # Add nextPageToken for pagination (only after first page)
            if next_page_token:
                payload["nextPageToken"] = next_page_token
            
            # POST request (not GET)
            response = self._request(
                "POST",
                f"{self.base_url}/rest/api/{self.api_version}/search/jql",
                json_payload=payload
            )

            data = response.json()
            issues = data.get("issues", [])
            is_last = data.get("isLast", True)
            next_page_token = data.get("nextPageToken")

            if not issues:
                break

            for issue in issues:
                yield JiraIssue(key=issue.get("key"), fields=issue.get("fields", {}))
                fetched += 1
                if limit and fetched >= limit:
                    return

            # Check if last page
            if is_last or not next_page_token:
                break

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _page_size_for_limit(self, limit: Optional[int], fetched: int) -> int:
        if limit is None:
            return self.page_size
        remaining = max(limit - fetched, 0)
        return min(self.page_size, remaining or self.page_size)
    def _request(self, method: str, url: str, params: Optional[Dict] = None, json_payload: Optional[Dict] = None) -> Response:
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # Build request kwargs
                kwargs = {"timeout": self.timeout}
                
                # Add params for GET requests
                if params:
                    kwargs["params"] = {k: v for k, v in params.items() if v is not None}
                
                # Add JSON payload for POST requests
                if json_payload:
                    kwargs["json"] = json_payload
                
                response = self.session.request(method, url, **kwargs)

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
