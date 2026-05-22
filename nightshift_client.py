"""
REST API client for the NightShift AGI marketplace.
"""

import requests
from config import NIGHTSHIFT_API_BASE, REQUEST_TIMEOUT


class NightShiftClient:
    """Client for interacting with the NightShift AGI REST API."""

    def __init__(self):
        """Initialize the client with a shared session and default headers."""
        self.base_url = NIGHTSHIFT_API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "NightShift-Work-Agent/1.0",
        })

    def _get(self, path):
        """
        Perform a GET request against the NightShift API.
        Returns the parsed JSON body on success.
        Raises RuntimeError on connection, timeout, or HTTP errors.
        """
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                f"Connection failed for {url}. Check your network and that nightshift-agi.com is reachable."
            ) from exc
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Request timed out after {REQUEST_TIMEOUT}s: {url}"
            ) from None
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(
                f"HTTP {response.status_code} from {url}: {exc}"
            ) from exc
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid JSON in response from {url}"
            ) from exc

    def get_jobs(self):
        """Fetch all available jobs from the marketplace."""
        return self._get("/jobs")

    def get_job(self, job_id):
        """Fetch details for a single job by ID."""
        return self._get(f"/jobs/{job_id}")

    def get_services(self):
        """Fetch all available services from the marketplace."""
        return self._get("/services")

    def get_profiles(self):
        """Fetch all registered profiles from the marketplace."""
        return self._get("/profiles")
