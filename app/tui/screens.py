from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Callable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog

from app.tui.api_client import ApiError, BackendApiClient


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class MainScreen(Screen[None]):
    BINDINGS = [("q", "app.quit", "Quit")]

    def __init__(self, api_client: BackendApiClient) -> None:
        super().__init__()
        self.api_client = api_client

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with Vertical(classes="section"):
                yield Label("Create customer")
                yield Input(placeholder="Name", id="customer-name")
                yield Input(placeholder="Email (@example.com)", id="customer-email")
                yield Button("Create customer", id="add-customer", variant="primary")

            with Vertical(classes="section"):
                yield Label("Create table/resource")
                yield Input(placeholder="Table name", id="table-name")
                yield Input(placeholder="Capacity", id="table-capacity")
                yield Button("Create table", id="add-table", variant="primary")

            with Vertical(classes="section"):
                yield Label("Create booking")
                yield Input(placeholder="Customer id", id="booking-customer-id")
                yield Input(placeholder="Resource id", id="booking-resource-id")
                yield Input(placeholder="Start (YYYY-MM-DD HH:MM:SS)", id="booking-start")
                yield Input(placeholder="End (YYYY-MM-DD HH:MM:SS)", id="booking-end")
                yield Button("Create booking", id="create-booking", variant="primary")

            with Vertical(classes="section"):
                yield Label("Find available tables")
                yield Input(
                    placeholder="Start (YYYY-MM-DD HH:MM:SS, blank = now)",
                    id="available-start",
                )
                yield Input(
                    placeholder="End (YYYY-MM-DD HH:MM:SS, blank = start + 2h)",
                    id="available-end",
                )
                yield Button("Find available tables", id="find-available")

            with Vertical(classes="section"):
                yield Label("Bookings")
                with Horizontal():
                    yield Button("List all bookings", id="list-bookings")
                    yield Button("List tables", id="list-tables")

            with Vertical(classes="section"):
                yield Label("Cancel booking")
                yield Input(placeholder="Booking id", id="cancel-booking-id")
                yield Button("Cancel booking", id="cancel-booking", variant="error")

        yield RichLog(id="output", wrap=True, highlight=True, markup=False)
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        handlers: dict[str, Callable[[], None]] = {
            "add-customer": self._add_customer,
            "add-table": self._add_table,
            "create-booking": self._create_booking,
            "find-available": self._find_available_tables,
            "list-bookings": self._list_bookings,
            "list-tables": self._list_tables,
            "cancel-booking": self._cancel_booking,
        }

        handler = handlers.get(event.button.id or "")
        if handler is None:
            return

        try:
            handler()
        except ApiError as error:
            self._write_error(str(error))
        except ValueError as error:
            self._write_error(str(error))

    def _add_customer(self) -> None:
        name = self._value("customer-name")
        email = self._value("customer-email")
        payload = self.api_client.create_customer(name=name, email=email)
        self._clear_inputs("customer-name", "customer-email")
        self._write_data("Customer created", payload)

    def _add_table(self) -> None:
        tablename = self._value("table-name")
        capacity = self._int_value("table-capacity")
        payload = self.api_client.create_table(
            capacity=capacity,
            tablename=tablename,
            active=True,
        )
        self._clear_inputs("table-name", "table-capacity")
        self._write_data("Table created", payload)

    def _list_tables(self) -> None:
        payload = self.api_client.list_tables()
        self._write_data("Tables", payload)

    def _find_available_tables(self) -> None:
        start_default = datetime.now().replace(microsecond=0)
        start_time = self._datetime_value("available-start", default=start_default)
        end_time = self._datetime_value(
            "available-end",
            default=start_default + timedelta(hours=2),
        )
        payload = self.api_client.list_available_tables(
            start_time=start_time,
            end_time=end_time,
        )
        self._write_data("Available tables", payload)

    def _create_booking(self) -> None:
        customer_id = self._int_value("booking-customer-id")
        resource_id = self._int_value("booking-resource-id")
        start_time = self._datetime_value("booking-start")
        end_time = self._datetime_value("booking-end")
        payload = self.api_client.create_booking(
            customer_id=customer_id,
            resource_id=resource_id,
            start_time=start_time,
            end_time=end_time,
        )
        self._clear_inputs(
            "booking-customer-id",
            "booking-resource-id",
            "booking-start",
            "booking-end",
        )
        self._write_data("Booking created", payload)

    def _list_bookings(self) -> None:
        payload = self.api_client.list_bookings()
        self._write_data("Bookings", payload)

    def _cancel_booking(self) -> None:
        booking_id = self._int_value("cancel-booking-id")
        self.api_client.cancel_booking(booking_id=booking_id)
        self._clear_inputs("cancel-booking-id")
        self._write_data("Booking cancelled", {"booking_id": booking_id})

    def _value(self, widget_id: str) -> str:
        value = self.query_one(f"#{widget_id}", Input).value.strip()
        if not value:
            raise ValueError(f"{widget_id} is required")
        return value

    def _int_value(self, widget_id: str) -> int:
        raw_value = self._value(widget_id)
        try:
            return int(raw_value)
        except ValueError as error:
            raise ValueError(f"{widget_id} must be an integer") from error

    def _datetime_value(
        self,
        widget_id: str,
        *,
        default: datetime | None = None,
    ) -> str:
        raw_value = self.query_one(f"#{widget_id}", Input).value.strip()
        if not raw_value:
            if default is None:
                raise ValueError(f"{widget_id} is required")
            return default.strftime(DATETIME_FORMAT)
        try:
            parsed = datetime.strptime(raw_value, DATETIME_FORMAT)
        except ValueError as error:
            raise ValueError(
                f"{widget_id} must use format {DATETIME_FORMAT}"
            ) from error
        return parsed.strftime(DATETIME_FORMAT)

    def _clear_inputs(self, *widget_ids: str) -> None:
        for widget_id in widget_ids:
            self.query_one(f"#{widget_id}", Input).value = ""

    def _write_data(self, title: str, payload: Any) -> None:
        output = self.query_one("#output", RichLog)
        output.write(f"\n[{title}]")
        output.write(json.dumps(payload, indent=2, default=str))

    def _write_error(self, message: str) -> None:
        output = self.query_one("#output", RichLog)
        output.write(f"\n[Error] {message}")

