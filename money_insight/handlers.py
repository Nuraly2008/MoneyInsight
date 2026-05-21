"""Telegram message and callback handlers for MoneyInsight."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

from .ai_classifier import CATEGORIES, save_merchant
from .balance_reader import extract_account_balance
from .charts import create_pie_chart
from .config import TEMP_DIR, ensure_directories
from .database import get_latest_report, get_user_reports, save_full_report
from .keyboards import main_menu, start_menu
from .keyboards.inline_keyboards import (
    category_choice_keyboard,
    expense_categories_keyboard,
    history_keyboard,
    report_keyboard,
    statistics_keyboard,
    transactions_keyboard,
)
from .pdf_reader import analyze_pdf
from .report_utils import short_text

logger = logging.getLogger(__name__)
router = Router()

# Fast cache for current session. Reports are also saved in SQLite.
user_reports: dict[int, dict[str, Any]] = {}
pending_merchants: dict[int, str] = {}

WELCOME_TEXT = (
    "👋 <b>Welcome to MoneyInsight!</b>\n\n"
    "Send me a Kaspi Gold PDF statement and I will calculate income, "
    "expenses, account balance, categories and statistics."
)

HELP_TEXT = (
    "<b>How to use MoneyInsight</b>\n\n"
    "1. Press <b>📊 Analyze Statement</b>.\n"
    "2. Upload your Kaspi PDF statement.\n"
    "3. Open <b>📈 Statistics</b>, <b>📂 Transactions</b>, "
    "<b>📊 Expenses by Category</b> or <b>🖼 Expense Chart (%)</b>.\n\n"
    "Commands: /start, /help, /stats, /transactions, /history, /new"
)


def _get_cached_or_latest_report(user_id: int) -> dict[str, Any] | None:
    if user_id in user_reports:
        return user_reports[user_id]

    report = get_latest_report(user_id)
    if report:
        user_reports[user_id] = report

    return report


async def _send_no_report_message(message: Message) -> None:
    await message.answer(
        "I do not have a report yet. Upload a Kaspi PDF statement first.",
        reply_markup=start_menu,
    )


def _save_report(
    user_id: int,
    income: float,
    expense: float,
    balance: float,
    transactions: list[dict[str, Any]],
) -> int:
    return save_full_report(
        user_id=user_id,
        income=income,
        expense=expense,
        balance=balance,
        transactions=transactions,
    )


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=start_menu)


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Help")
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu)


@router.message(Command("new"))
@router.message(F.text == "📊 Analyze Statement")
@router.message(F.text == "🔄 New Analysis")
async def analyze_button(message: Message) -> None:
    await message.answer("Upload your Kaspi PDF statement.", reply_markup=start_menu)


@router.message(F.document)
async def document_handler(message: Message) -> None:
    document = message.document
    file_name = document.file_name or "statement.pdf"

    if not file_name.lower().endswith(".pdf"):
        await message.answer("Please upload a PDF file, not another format.")
        return

    ensure_directories()
    safe_name = f"{message.from_user.id}_{document.file_unique_id}.pdf"
    file_path = TEMP_DIR / safe_name

    status_message = await message.answer(
        "⏳ Reading your PDF and calculating the report..."
    )

    try:
        await message.bot.download(document, destination=file_path)
        account_balance = extract_account_balance(file_path)
        data = analyze_pdf(file_path)

    except Exception as exc:
        logger.exception("PDF analysis failed")
        await status_message.edit_text(
            "I could not analyze this file. Please make sure it is a Kaspi Gold "
            "statement PDF and try again.\n\n"
            f"Error: <code>{short_text(str(exc), 120)}</code>"
        )
        return

    finally:
        try:
            Path(file_path).unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove temporary file %s", file_path)

    income = float(data["income"])
    expense = float(data["expense"])
    balance = float(account_balance if account_balance is not None else income - expense)
    transactions = data["transactions"]
    unknown_merchants = data["unknown_merchants"]

    report_id = _save_report(
        user_id=message.from_user.id,
        income=income,
        expense=expense,
        balance=balance,
        transactions=transactions,
    )

    user_reports[message.from_user.id] = {
        "id": report_id,
        "income": income,
        "expense": expense,
        "balance": balance,
        "transactions": transactions,
    }

    await status_message.edit_text("✅ Done! Here is your financial report.")
    await message.answer(
        "<b>Financial Report</b>",
        reply_markup=report_keyboard(income, expense, balance),
    )
    await message.answer(
        "<b>📊 Expenses by Category</b>",
        reply_markup=expense_categories_keyboard(transactions),
    )
    await message.answer("Choose function:", reply_markup=main_menu)

    if unknown_merchants:
        merchant = unknown_merchants[0]
        pending_merchants[message.from_user.id] = merchant
        await message.answer(
            "I found an unknown merchant and can learn it for the next reports:\n\n"
            f"<b>{merchant}</b>\n\nChoose category:",
            reply_markup=category_choice_keyboard(),
        )


@router.callback_query(F.data == "noop")
async def empty_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query()
async def category_callback(callback: CallbackQuery) -> None:
    data = callback.data or ""
    category = data.replace("cat:", "", 1) if data.startswith("cat:") else data

    if category not in CATEGORIES:
        await callback.answer()
        return

    user_id = callback.from_user.id
    merchant = pending_merchants.get(user_id)

    if not merchant:
        await callback.answer("No merchant is waiting for category selection.")
        return

    save_merchant(merchant, category)
    del pending_merchants[user_id]

    await callback.message.answer(f"Saved:\n<b>{merchant}</b>\n→ {category}")
    await callback.answer("Saved")


@router.message(Command("stats"))
@router.message(F.text == "📈 Statistics")
async def statistics_handler(message: Message) -> None:
    report = _get_cached_or_latest_report(message.from_user.id)

    if not report:
        await _send_no_report_message(message)
        return

    await message.answer(
        "<b>📈 Statistics</b>",
        reply_markup=statistics_keyboard(report),
    )


@router.message(Command("transactions"))
@router.message(F.text == "📂 Transactions")
async def transactions_handler(message: Message) -> None:
    report = _get_cached_or_latest_report(message.from_user.id)

    if not report:
        await _send_no_report_message(message)
        return

    await message.answer(
        "<b>📂 Last Transactions</b>",
        reply_markup=transactions_keyboard(report.get("transactions", [])),
    )


@router.message(F.text == "📊 Expenses by Category")
async def categories_handler(message: Message) -> None:
    report = _get_cached_or_latest_report(message.from_user.id)

    if not report:
        await _send_no_report_message(message)
        return

    await message.answer(
        "<b>📊 Expenses by Category</b>",
        reply_markup=expense_categories_keyboard(report.get("transactions", [])),
    )


@router.message(F.text == "🖼 Expense Chart (%)")
@router.message(F.text == "📊 Expense Chart")
async def expense_chart_handler(message: Message) -> None:
    report = _get_cached_or_latest_report(message.from_user.id)

    if not report:
        await _send_no_report_message(message)
        return

    chart_path = create_pie_chart(
        report.get("transactions", []),
        user_id=message.from_user.id,
    )

    await message.answer_photo(
        photo=FSInputFile(chart_path),
        caption="<b>🖼 Expense Chart (%)</b>",
    )


@router.message(Command("history"))
@router.message(F.text == "🕘 History")
async def history_handler(message: Message) -> None:
    history = get_user_reports(message.from_user.id, limit=5)

    if not history:
        await _send_no_report_message(message)
        return

    await message.answer(
        "<b>🕘 History</b>\nLast saved analyses:",
        reply_markup=history_keyboard(history),
    )


@router.message()
async def unknown_message(message: Message) -> None:
    await message.answer("Please choose a menu button or use /help.", reply_markup=main_menu)
