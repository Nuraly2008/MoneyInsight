"""SQLite storage layer for reports and transactions."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import ensure_directories, settings

# Kept for compatibility with the original in-memory project.
reports: list[dict[str, Any]] = []

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    income REAL NOT NULL,
    expense REAL NOT NULL,
    balance REAL NOT NULL DEFAULT 0,
    transaction_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    transaction_date TEXT,
    operation TEXT NOT NULL,
    merchant TEXT,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reports_user_created
    ON reports(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_report
    ON transactions(report_id);
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    ensure_directories()
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing_columns = {column["name"] for column in columns}

    if column_name not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        _ensure_column(connection, "reports", "balance", "REAL NOT NULL DEFAULT 0")
        _ensure_column(
            connection,
            "reports",
            "transaction_count",
            "INTEGER NOT NULL DEFAULT 0",
        )


def save_report(
    user_id: int,
    income: float,
    expense: float,
    balance: float | None = None,
) -> int:
    """Save a report summary and return its report_id."""
    init_db()
    created_at = _utc_now()
    clean_balance = income - expense if balance is None else balance

    with get_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users(user_id, created_at) VALUES (?, ?)",
            (user_id, created_at),
        )
        cursor = connection.execute(
            """
            INSERT INTO reports(user_id, income, expense, balance, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, income, expense, clean_balance, created_at),
        )
        report_id = int(cursor.lastrowid)

    reports.append(
        {
            "id": report_id,
            "user_id": user_id,
            "income": income,
            "expense": expense,
            "balance": clean_balance,
            "created_at": created_at,
        }
    )

    return report_id


def save_transactions(report_id: int, transactions: list[dict[str, Any]]) -> None:
    init_db()
    rows = [
        (
            report_id,
            item.get("date"),
            item.get("operation", ""),
            item.get("merchant", ""),
            item.get("category", "Other"),
            float(item.get("amount", 0)),
        )
        for item in transactions
    ]

    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO transactions(
                report_id, transaction_date, operation, merchant, category, amount
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.execute(
            "UPDATE reports SET transaction_count = ? WHERE id = ?",
            (len(rows), report_id),
        )


def save_full_report(
    user_id: int,
    income: float,
    expense: float,
    transactions: list[dict[str, Any]],
    balance: float | None = None,
) -> int:
    report_id = save_report(
        user_id=user_id,
        income=income,
        expense=expense,
        balance=balance,
    )
    save_transactions(report_id, transactions)
    return report_id


def get_report_transactions(report_id: int) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT transaction_date AS date, operation, merchant, category, amount
            FROM transactions
            WHERE report_id = ?
            ORDER BY id ASC
            """,
            (report_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_latest_report(user_id: int) -> dict[str, Any] | None:
    init_db()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, user_id, income, expense, balance, transaction_count, created_at
            FROM reports
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    report = dict(row)
    report["transactions"] = get_report_transactions(report["id"])
    return report


def get_user_reports(user_id: int, limit: int = 5) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, income, expense, balance, transaction_count, created_at
            FROM reports
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [dict(row) for row in rows]
