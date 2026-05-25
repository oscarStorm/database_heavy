from __future__ import annotations

from typing import Any, cast

import pymysql

from app.backend.db import get_connection


def list_customers() -> list[dict[str, Any]]:
    return _call_procedure_fetchall("list_customers")


def create_customer(name: str, email: str) -> dict[str, Any]:
    return _call_procedure_fetchone("create_customer", (name, email))


def list_tables() -> list[dict[str, Any]]:
    return _call_procedure_fetchall("list_resources")


def create_restaurant_table(
    capacity: int,
    tablename: str,
    active: bool,
) -> dict[str, Any]:
    return _call_procedure_fetchone(
        "create_restaurant_table",
        (capacity, tablename, active),
    )


def list_available_tables(
    start_time: str,
    end_time: str,
) -> list[dict[str, Any]]:
    return _call_procedure_fetchall(
        "list_available_resources",
        (start_time, end_time),
    )


def list_bookings() -> list[dict[str, Any]]:
    return _call_procedure_fetchall("list_bookings")


def list_bookings_for_table(resource_id: int) -> list[dict[str, Any]]:
    return _call_procedure_fetchall("list_bookings_for_resource", (resource_id,))


def create_booking(
    customer_id: int,
    resource_id: int,
    start_time: str,
    end_time: str,
) -> dict[str, Any]:
    return _call_procedure_fetchone(
        "create_booking",
        (customer_id, resource_id, start_time, end_time),
    )


def cancel_booking(booking_id: int) -> None:
    _call_procedure_fetchall("cancel_booking", (booking_id,))


def _call_procedure_fetchone(
    procedure_name: str,
    args: tuple[Any, ...] = (),
) -> dict[str, Any]:
    rows = _call_procedure_fetchall(procedure_name, args)
    if not rows:
        raise RuntimeError(f"Procedure {procedure_name} returned no rows")
    return rows[0]


def _call_procedure_fetchall(
    procedure_name: str,
    args: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    placeholders = ", ".join(["%s"] * len(args))
    sql = f"CALL {procedure_name}({placeholders})"

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args)
                rows = cast(list[dict[str, Any]], cursor.fetchall())
                _drain_result_sets(cursor)
                return rows
    except pymysql.MySQLError as error:
        raise ValueError(_database_error_message(error)) from error


def _drain_result_sets(cursor: pymysql.cursors.Cursor) -> None:
    while cursor.nextset():
        cursor.fetchall()


def _database_error_message(error: pymysql.MySQLError) -> str:
    error_args = getattr(error, "args", ())
    if len(error_args) >= 2:
        return str(error_args[1])
    return str(error)

