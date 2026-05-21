"""Kaspi PDF statement reader and analyzer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pdfplumber

from .ai_classifier import classify_transaction

DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{2,4}$")


def parse_amount(amount_text: str) -> float:
    """Parse Kaspi money strings like '- 1 100,00 ₸' into floats."""
    original = amount_text or ""
    cleaned = (
        original.replace("₸", "")
        .replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
        .strip()
    )
    sign = -1 if cleaned.startswith("-") or "-" in original else 1
    cleaned = cleaned.replace("+", "").replace("-", "")
    if not cleaned:
        raise ValueError("Empty amount")
    return sign * abs(float(cleaned))


def _clean_row(row: list[Any]) -> list[str]:
    return [str(cell or "").strip() for cell in row]


def _is_transaction_row(row: list[str]) -> bool:
    return len(row) >= 4 and bool(DATE_RE.match(row[0]))


def analyze_pdf(file_path: str | Path) -> dict[str, Any]:
    """Analyze a Kaspi statement PDF.

    The returned structure is compatible with the original bot:
    income, expense, transactions, unknown_merchants.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file was not found: {path}")

    transactions: list[dict[str, Any]] = []
    total_income = 0.0
    total_expense = 0.0
    unknown_merchants: list[str] = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                if not table:
                    continue

                for raw_row in table:
                    row = _clean_row(raw_row)
                    if not _is_transaction_row(row):
                        continue

                    date, amount_text, operation_type, details = row[:4]

                    try:
                        amount = parse_amount(amount_text)
                    except ValueError:
                        continue

                    category, merchant = classify_transaction(operation_type, details)
                    if category is None:
                        category = "Other"
                        if merchant and merchant not in unknown_merchants:
                            unknown_merchants.append(merchant)

                    operation = f"{operation_type} {details}".strip()

                    if amount > 0:
                        total_income += amount
                    else:
                        total_expense += abs(amount)

                    transactions.append(
                        {
                            "date": date,
                            "operation": operation,
                            "operation_type": operation_type,
                            "details": details,
                            "merchant": merchant,
                            "amount": amount,
                            "category": category,
                        }
                    )

    if not transactions:
        raise ValueError(
            "No transactions found. Make sure this is a Kaspi Gold statement PDF."
        )

    return {
        "income": total_income,
        "expense": total_expense,
        "transactions": transactions,
        "unknown_merchants": unknown_merchants,
    }
