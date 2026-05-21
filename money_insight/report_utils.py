"""Reusable report calculations and formatting helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def money(amount: float, keep_cents: bool = False) -> str:
    """Format tenge values for Telegram messages."""
    if keep_cents:
        value = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
        return f"{value} ₸"

    return f"{amount:,.0f} ₸".replace(",", " ")


def short_text(text: str, limit: int = 42) -> str:
    """Shorten long merchant names for inline buttons."""
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def operation_word(count: int) -> str:
    """Return singular/plural operation label."""
    return "operation" if count == 1 else "operations"


def expense_categories(transactions: list[dict[str, Any]]) -> dict[str, float]:
    """Return expense amount by category, sorted by highest spending."""
    categories: dict[str, float] = defaultdict(float)

    for item in transactions:
        amount = float(item.get("amount", 0))
        if amount < 0:
            category = item.get("category", "Other")
            categories[category] += abs(amount)

    return dict(sorted(categories.items(), key=lambda item: item[1], reverse=True))


def expense_categories_with_counts(
    transactions: list[dict[str, Any]],
) -> dict[str, dict[str, float | int]]:
    """Return expense amount and operation count by category."""
    categories: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"amount": 0.0, "count": 0}
    )

    for item in transactions:
        amount = float(item.get("amount", 0))
        if amount < 0:
            category = item.get("category", "Other")
            categories[category]["amount"] = float(categories[category]["amount"]) + abs(amount)
            categories[category]["count"] = int(categories[category]["count"]) + 1

    return dict(
        sorted(
            categories.items(),
            key=lambda item: float(item[1]["amount"]),
            reverse=True,
        )
    )


def daily_average(expense: float, transactions: list[dict[str, Any]]) -> float:
    """Calculate average spending per active statement day."""
    days = {item.get("date") for item in transactions if item.get("date")}
    return expense / max(len(days), 1)
