from __future__ import annotations

import os
import statistics
import threading
import time
import unittest
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx
from app.backend.db import get_connection
from app.tui.api_client import BackendApiClient


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class TuiToDatabaseLatencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
        cls.client = BackendApiClient(base_url=base_url)
        try:
            cls.client._client.get("/")
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
        except (httpx.HTTPError, OSError, Exception) as error:
            cls.client.close()
            raise unittest.SkipTest(
                f"Benchmark requires running backend and database: {error}"
            ) from error

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()

    def test_booking_visibility_latency(self) -> None:
        iterations = int(os.getenv("LATENCY_ITERATIONS", "50"))
        warmup_iterations = int(os.getenv("LATENCY_WARMUP_ITERATIONS", "2"))
        poll_interval = float(os.getenv("LATENCY_POLL_INTERVAL", "0.001"))
        results: list[dict[str, float]] = []

        for index in range(warmup_iterations):
            self._measure_booking(index=index, poll_interval=poll_interval)

        for index in range(iterations):
            results.append(
                self._measure_booking(
                    index=index + warmup_iterations,
                    poll_interval=poll_interval,
                )
            )

        response_values = [row["response_ms"] for row in results]
        visible_values = [row["visible_ms"] for row in results]

        print()
        print("booking_visibility_latency_ms")
        print(f"  warmup_runs={warmup_iterations} measured_runs={iterations}")
        for index, row in enumerate(results, start=1):
            print(
                f"  run={index} response={row['response_ms']:.3f} "
                f"visible={row['visible_ms']:.3f}"
            )
        print(
            f"  avg response={statistics.fmean(response_values):.3f} "
            f"visible={statistics.fmean(visible_values):.3f}"
        )
        print(
            f"  median response={statistics.median(response_values):.3f} "
            f"visible={statistics.median(visible_values):.3f}"
        )
        print(
            f"  p95 response={self._percentile(response_values, 0.95):.3f} "
            f"visible={self._percentile(visible_values, 0.95):.3f}"
        )
        print(
            f"  min response={min(response_values):.3f} "
            f"visible={min(visible_values):.3f}"
        )
        print(
            f"  max response={max(response_values):.3f} "
            f"visible={max(visible_values):.3f}"
        )

    def _measure_booking(self, *, index: int, poll_interval: float) -> dict[str, float]:
        run_id = uuid4().hex[:8]
        customer = self.client.create_customer(
            name=f"Latency User {run_id}",
            email=f"latency_{run_id}@example.com",
        )
        resource = self.client.create_table(
            capacity=2,
            tablename=f"Latency Table {run_id}",
            active=True,
        )

        start_time = (
            datetime.now().replace(microsecond=0)
            + timedelta(days=1, minutes=index * 10)
        )
        end_time = start_time + timedelta(hours=2)
        booking_key = {
            "customer_id": int(customer["id"]),
            "resource_id": int(resource["id"]),
            "start_time": start_time.strftime(DATETIME_FORMAT),
            "end_time": end_time.strftime(DATETIME_FORMAT),
        }

        ready = threading.Event()
        detected = threading.Event()
        result_box: dict[str, Any] = {}
        watcher = threading.Thread(
            target=self._watch_booking_visibility,
            args=(booking_key, ready, detected, result_box, poll_interval),
            daemon=True,
        )
        watcher.start()
        ready.wait(timeout=2)

        started_ns = time.perf_counter_ns()
        booking = self.client.create_booking(**booking_key)
        responded_ns = time.perf_counter_ns()

        self.assertTrue(
            detected.wait(timeout=5),
            "Booking never became visible in the database",
        )
        watcher.join(timeout=1)

        visible_ns = int(result_box["visible_ns"])
        response_ms = (responded_ns - started_ns) / 1_000_000
        visible_ms = (visible_ns - started_ns) / 1_000_000

        self.assertEqual(int(booking["id"]), int(result_box["booking_id"]))
        return {
            "response_ms": response_ms,
            "visible_ms": visible_ms,
        }

    def _watch_booking_visibility(
        self,
        booking_key: dict[str, Any],
        ready: threading.Event,
        detected: threading.Event,
        result_box: dict[str, Any],
        poll_interval: float,
    ) -> None:
        sql = """
        SELECT id
        FROM bookings
        WHERE customer_id = %s
          AND resource_id = %s
          AND start_time = %s
          AND end_time = %s
        """

        ready.set()
        while not detected.is_set():
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        (
                            booking_key["customer_id"],
                            booking_key["resource_id"],
                            booking_key["start_time"],
                            booking_key["end_time"],
                        ),
                    )
                    row = cursor.fetchone()
                    if row is not None:
                        result_box["booking_id"] = row["id"]
                        result_box["visible_ns"] = time.perf_counter_ns()
                        detected.set()
                        return
            time.sleep(poll_interval)

    @staticmethod
    def _percentile(values: list[float], quantile: float) -> float:
        if len(values) == 1:
            return values[0]
        ordered = sorted(values)
        position = (len(ordered) - 1) * quantile
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


if __name__ == "__main__":
    unittest.main()
