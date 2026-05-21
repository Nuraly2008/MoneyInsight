"""Extract real account balance from Kaspi PDF statements."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)

BALANCE_RE = re.compile(
    r"Сумма\s+на\s+счете\s+в\s+тенге.*?₸?\s*([0-9][0-9\s]*,\d{2})",
    re.IGNORECASE | re.DOTALL,
)


def parse_pdf_money(text: str) -> float:
    """Parse strings like '₸ 167,75' into 167.75."""
    cleaned = (
        text.replace("₸", "")
        .replace("\u00a0", " ")
        .replace(" ", "")
        .replace(",", ".")
        .replace("+", "")
        .strip()
    )

    if not cleaned:
        raise ValueError("Empty money value")

    return float(cleaned)


def _clean_table_rows(table: list[list[Any]]) -> list[list[str]]:
    return [[str(cell or "").strip() for cell in row] for row in table]


def _extract_from_table(table: list[list[Any]]) -> float | None:
    rows = _clean_table_rows(table)

    for index, row in enumerate(rows):
        row_text = " ".join(row).lower()

        if "сумма на счете в тенге" not in row_text:
            continue

        if index + 1 >= len(rows):
            continue

        for cell in rows[index + 1]:
            try:
                return parse_pdf_money(cell)
            except ValueError:
                continue

    return None


def extract_account_balance(file_path: str | Path) -> float | None:
    """Extract 'Сумма на счете в тенге' from a Kaspi PDF.

    This is the real account balance from the statement, not income minus expenses.
    Returns None when the field is not found, so the bot can use a safe fallback.
    """
    try:
        with pdfplumber.open(str(file_path)) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            match = BALANCE_RE.search(full_text)

            if match:
                return parse_pdf_money(match.group(1))

            for page in pdf.pages:
                for table in page.extract_tables() or []:
                    balance = _extract_from_table(table)
                    if balance is not None:
                        return balance

    except Exception as exc:
        logger.warning("Could not extract account balance from PDF: %s", exc)

    return None
