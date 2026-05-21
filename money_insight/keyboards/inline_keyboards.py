"""Inline keyboards used in reports, statistics, categories and history."""

from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..config import settings
from ..report_utils import (
    daily_average,
    expense_categories,
    expense_categories_with_counts,
    money,
    operation_word,
    short_text,
)

CATEGORY_EMOJI = {
    "Food": "🍔",
    "Transport": "🚌",
    "Shopping": "🛍",
    "Entertainment": "🎮",
    "Travel": "✈️",
    "Subscriptions": "📱",
    "Cash Withdrawal": "🏧",
    "Transfers": "🔁",
    "Income": "💰",
    "Other": "📦",
}

LEARNABLE_CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Entertainment",
    "Travel",
    "Subscriptions",
    "Transfers",
    "Cash Withdrawal",
    "Other",
]


def report_keyboard(income: float, expense: float, balance: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"💰 Income: {money(income)}", callback_data="noop")],
            [InlineKeyboardButton(text=f"💸 Expenses: {money(expense)}", callback_data="noop")],
            [
                InlineKeyboardButton(
                    text=f"🏦 Account balance: {money(balance, keep_cents=True)}",
                    callback_data="noop",
                )
            ],
        ]
    )


def expense_categories_keyboard(transactions: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    categories = expense_categories_with_counts(transactions)
    buttons: list[list[InlineKeyboardButton]] = []

    if not categories:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="No expenses found", callback_data="noop")]
            ]
        )

    total_amount = 0.0
    total_operations = 0

    for category, data in categories.items():
        amount = float(data["amount"])
        count = int(data["count"])
        total_amount += amount
        total_operations += count

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{CATEGORY_EMOJI.get(category, '•')} {category}: {money(amount)} "
                        f"• {count} {operation_word(count)}"
                    ),
                    callback_data="noop",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text=(
                    f"💸 Total expenses: {money(total_amount)} "
                    f"• {total_operations} {operation_word(total_operations)}"
                ),
                callback_data="noop",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def transactions_keyboard(transactions: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    preview = transactions[-settings.max_transactions_preview :][::-1]
    buttons: list[list[InlineKeyboardButton]] = []

    for item in preview:
        amount = float(item.get("amount", 0))
        sign = "+" if amount > 0 else "-"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{item.get('date', '')} | {sign}{money(abs(amount))} | "
                        f"{item.get('category', 'Other')} | {short_text(item.get('merchant', ''))}"
                    ),
                    callback_data="noop",
                )
            ]
        )

    if not buttons:
        buttons = [[InlineKeyboardButton(text="No transactions", callback_data="noop")]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def category_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{CATEGORY_EMOJI.get(category, '•')} {category}",
                    callback_data=f"cat:{category}",
                )
            ]
            for category in LEARNABLE_CATEGORIES
        ]
    )


def statistics_keyboard(report: dict[str, Any]) -> InlineKeyboardMarkup:
    income = float(report["income"])
    expense = float(report["expense"])
    balance = float(report.get("balance", income - expense))
    transactions = report.get("transactions", [])

    expenses_only = [item for item in transactions if float(item.get("amount", 0)) < 0]
    largest = max(
        expenses_only,
        key=lambda x: abs(float(x.get("amount", 0))),
        default=None,
    )

    categories = expense_categories(transactions)
    top_category = next(iter(categories.items()), None)

    buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=f"💰 Income: {money(income)}", callback_data="noop")],
        [InlineKeyboardButton(text=f"💸 Expenses: {money(expense)}", callback_data="noop")],
        [
            InlineKeyboardButton(
                text=f"🏦 Account balance: {money(balance, keep_cents=True)}",
                callback_data="noop",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📅 Average per day: {money(daily_average(expense, transactions))}",
                callback_data="noop",
            )
        ],
    ]

    if largest:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"🔥 Largest expense: {money(abs(float(largest['amount'])))} | "
                        f"{short_text(largest.get('merchant', ''))}"
                    ),
                    callback_data="noop",
                )
            ]
        )

    if top_category:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🏆 Top category: {top_category[0]} ({money(top_category[1])})",
                    callback_data="noop",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def history_keyboard(history: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []

    for index, item in enumerate(history, start=1):
        created_at = str(item.get("created_at", "")).replace("T", " ")[:16]
        income = float(item["income"])
        expense = float(item["expense"])
        balance = float(item.get("balance", income - expense))
        transaction_count = int(item["transaction_count"])

        buttons.append(
            [InlineKeyboardButton(text=f"{index}. 🕘 {created_at}", callback_data="noop")]
        )
        buttons.append(
            [
                InlineKeyboardButton(text=f"💰 Income: {money(income)}", callback_data="noop"),
                InlineKeyboardButton(text=f"💸 Expenses: {money(expense)}", callback_data="noop"),
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🏦 Balance: {money(balance, keep_cents=True)}",
                    callback_data="noop",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📂 Transactions: {transaction_count}",
                    callback_data="noop",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
