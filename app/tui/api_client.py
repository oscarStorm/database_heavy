from __future__ import annotations

from typing import Any

import httpx


class ApiError(Exception):
    pass


class BackendApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self._client = httpx.Client(base_url=base_url, timeout=10.0)

    def close(self) -> None:
        self._client.close()

    def list_customers(self) -> list[dict[str, Any]]:
        return self._request("GET", "/customers")

    def create_customer(self, name: str, email: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/customers",
            json={"name": name, "email": email},
        )

    def list_tables(self) -> list[dict[str, Any]]:
        return self._request("GET", "/resources")

    def create_table(self, capacity: int, tablename: str, active: bool) -> dict[str, Any]:
        return self._request(
            "POST",
            "/resources",
            json={
                "capacity": capacity,
                "tablename": tablename,
                "active": active,
            },
        )

    def list_available_tables(
        self,
        start_time: str,
        end_time: str,
    ) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/resources/available",
            params={"start_time": start_time, "end_time": end_time},
        )

    def list_table_bookings(self, resource_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/resources/{resource_id}/bookings")

    def list_bookings(self) -> list[dict[str, Any]]:
        return self._request("GET", "/booking")

    def create_booking(
        self,
        customer_id: int,
        resource_id: int,
        start_time: str,
        end_time: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/booking",
            json={
                "customer_id": customer_id,
                "resource_id": resource_id,
                "start_time": start_time,
                "end_time": end_time,
            },
        )

    def cancel_booking(self, booking_id: int) -> None:
        self._request("DELETE", f"/booking/{booking_id}", expect_json=False)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        expect_json: bool = True,
    ) -> Any:
        response = self._client.request(method, path, params=params, json=json)

        if response.is_error:
            detail = self._extract_error_detail(response)
            raise ApiError(detail)

        if not expect_json or response.status_code == 204:
            return None

        return response.json()

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"HTTP {response.status_code}: {response.text}"

        if isinstance(payload, dict) and "detail" in payload:
            return str(payload["detail"])

        return f"HTTP {response.status_code}: {payload}"

