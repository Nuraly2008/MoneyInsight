"""Chart generation for MoneyInsight reports."""

from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .config import CHARTS_DIR, ensure_directories


def _format_tenge(amount: float) -> str:
    return f"{amount:,.0f} ₸".replace(",", " ")


def _show_percent(percent: float) -> str:
    """Show percentage only if slice is big enough."""
    if percent < 3:
        return ""
    return f"{percent:.1f}%"


def create_pie_chart(transactions: list[dict], user_id: int | None = None) -> str:
    """Create an expense pie chart and return the image path."""
    ensure_directories()

    categories: dict[str, float] = defaultdict(float)

    for item in transactions:
        amount = float(item.get("amount", 0))

        if amount < 0:
            category = item.get("category", "Other")
            categories[category] += abs(amount)

    filename_user = f"{user_id}_" if user_id else ""
    chart_path = CHARTS_DIR / f"expenses_{filename_user}{uuid4().hex[:10]}.png"

    fig, ax = plt.subplots(figsize=(10, 7))

    if categories:
        sorted_items = sorted(
            categories.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        total = sum(values)

        wedges, _, autotexts = ax.pie(
            values,
            labels=None,
            autopct=_show_percent,
            startangle=90,
            pctdistance=0.7,
            wedgeprops={
                "linewidth": 1,
                "edgecolor": "white",
            },
        )

        for text in autotexts:
            text.set_fontsize(11)
            text.set_weight("bold")

        legend_labels = [
            f"{label}: {_format_tenge(value)} ({value / total * 100:.1f}%)"
            for label, value in zip(labels, values)
        ]

        ax.legend(
            wedges,
            legend_labels,
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize=10,
        )

        ax.set_title("Expenses by Category (%)", fontsize=16, pad=20)
        ax.axis("equal")

    else:
        ax.text(
            0.5,
            0.5,
            "No expenses found",
            ha="center",
            va="center",
            fontsize=14,
        )
        ax.axis("off")

    plt.tight_layout()
    plt.savefig(chart_path, dpi=180, bbox_inches="tight")
    plt.close()

    return str(chart_path)