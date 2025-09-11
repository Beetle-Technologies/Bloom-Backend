from functools import lru_cache
from typing import Literal, Optional

import httpx


@lru_cache(maxsize=1)
class RequestService:
    _instance: Optional["RequestService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RequestService, cls).__new__(cls)
        return cls._instance

    async def make_request(
        self,
        *,
        url: str,
        method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
        headers: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Makes an HTTP request to the specified URL with the given method and headers.

        Args:
            url (str): The URL to send the request to.
            method (Literal["GET", "POST", "PUT", "DELETE"], optional): The HTTP method to use. Defaults to "GET".
            headers (Optional[dict], optional): Optional headers to include in the request. Defaults to None.

        Returns:
            Optional[dict]: The JSON response as a dictionary if the request is successful, otherwise None
        """

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, headers=headers, timeout=5)
                if response.status_code != 200:
                    return None
                return response.json()
        except Exception:
            return None

    async def get_location(self, ip_address: str) -> str:
        """
        Make a request to an IP geolocation service to get the location of the given IP address.

        Args:
            ip_address (str): The IP address to look up.

        Returns:
            str: A string representing the location (city, region, country) or "N/A
        """

        url = f"https://ipapi.co/{ip_address}/json/"
        try:
            response = await self.make_request(url=url, method="GET")
            if response is None:
                return "N/A"
            city = response.get("city")
            region = response.get("region")
            country = response.get("country_name")
            parts = [part for part in [city, region, country] if part]
            if parts:
                return ", ".join(parts)
            return "N/A"
        except Exception:
            return "N/A"


request_service = RequestService()
