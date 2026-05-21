"""Merchant normalization and transaction categorization logic."""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from typing import Optional, Tuple

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - the bot can work without AI fallback
    OpenAI = None  # type: ignore

from .config import ensure_directories, settings

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Entertainment",
    "Travel",
    "Subscriptions",
    "Transfers",
    "Cash Withdrawal",
    "Income",
    "Other",
]

BASE_MERCHANTS = {
    # Food / grocery / cafe
    "MAGNUM": "Food",
    "SMALL": "Food",
    "FOODBAZA": "Food",
    "QUT": "Food",
    "DONER": "Food",
    "КОФЕЙНЯ": "Food",
    "РУМАКС": "Food",
    "LEMON": "Food",
    "ТАБЫС": "Food",
    "ДОС": "Food",
    "МИНИ МАРКЕТ": "Food",
    "AI-MARKET": "Food",
    "АI-MARKET": "Food",
    "TMRS": "Food",
    # Transport
    "AVTOBYS": "Transport",
    "YANDEX GO": "Transport",
    "YANDEX.TAXI": "Transport",
    "ASTANA LRT": "Transport",
    "LRT": "Transport",
    # Shopping
    "WILDBERRIES": "Shopping",
    "DEFACTO": "Shopping",
    "KASPI MAGAZIN": "Shopping",
    # Subscriptions
    "APPLE": "Subscriptions",
    "YANDEX.PLUS": "Subscriptions",
    "SPOTIFY": "Subscriptions",
    "NETFLIX": "Subscriptions",
    # Travel
    "KASPI TRAVEL": "Travel",
    "AIR ASTANA": "Travel",
    "FLYARYSTAN": "Travel",
    # Entertainment
    "CYBER": "Entertainment",
    "G-HOUSE": "Entertainment",
    "КИНО": "Entertainment",
    "МУЗЕЙ": "Entertainment",
    "MUSEUM": "Entertainment",
}

LEGAL_FORMS_RE = re.compile(r'\b(ИП|ТОО|АО|LLP|IP|TOO)\b|["“”«»]')
MULTISPACE_RE = re.compile(r"\s+")


# Kept for compatibility with the original project.
MERCHANTS_FILE = str(settings.merchants_file)


def _ensure_merchants_file() -> None:
    ensure_directories()
    if not settings.merchants_file.exists():
        settings.merchants_file.write_text("{}", encoding="utf-8")


def load_merchants() -> dict[str, str]:
    """Load merchant categories learned from user feedback."""
    _ensure_merchants_file()
    try:
        with settings.merchants_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, dict):
                return {str(k).upper(): str(v) for k, v in data.items()}
    except json.JSONDecodeError:
        logger.warning("Merchants file is corrupted. Recreating an empty file.")
    except OSError as exc:
        logger.error("Could not read merchants file: %s", exc)

    settings.merchants_file.write_text("{}", encoding="utf-8")
    return {}


def save_merchant(merchant: str, category: str) -> None:
    """Save a merchant-category pair selected by the user."""
    normalized = normalize_merchant(merchant)
    clean_category = category if category in CATEGORIES else "Other"

    data = load_merchants()
    data[normalized] = clean_category

    _ensure_merchants_file()
    with settings.merchants_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4, sort_keys=True)


def normalize_merchant(details: str) -> str:
    """Convert noisy Kaspi transaction details into a stable merchant key."""
    text = (details or "").upper()
    text = text.replace("\n", " ").replace(".", " ").replace(",", " ")
    text = LEGAL_FORMS_RE.sub(" ", text)
    text = MULTISPACE_RE.sub(" ", text).strip()

    bad_words = {
        "SHOP",
        "STORE",
        "MARKET",
        "МАРКЕТ",
        "АТЕЛЬЕ",
        "TERMINAL",
        "ТЕРМИНАЛ",
        "САМООБСЛУЖИВАНИЯ",
    }

    words = [word for word in text.split() if word not in bad_words]
    return " ".join(words[:3]) if words else text


@lru_cache(maxsize=256)
def ai_guess_category(merchant: str) -> str:
    """Use OpenRouter AI as an optional fallback for unknown merchants.

    The function is cached to avoid repeated paid/API calls for the same merchant.
    If no API key is configured, the bot still works and returns "Other".
    """
    if not merchant:
        return "Other"
    if not settings.openrouter_api_key or OpenAI is None:
        return "Other"

    try:
        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        response = client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify a bank transaction merchant into exactly one "
                        "category: Food, Transport, Shopping, Entertainment, "
                        "Travel, Subscriptions, Other. Return only the category."
                    ),
                },
                {"role": "user", "content": merchant},
            ],
            temperature=0,
        )
        category = response.choices[0].message.content.strip()
        return category if category in CATEGORIES else "Other"
    except Exception as exc:  # network/API failures should not break analysis
        logger.warning("AI categorization failed for %s: %s", merchant, exc)
        return "Other"


def classify_transaction(operation_type: str, details: str) -> Tuple[Optional[str], str]:
    """Classify one Kaspi transaction.

    Returns (category, merchant). Category can be None when user feedback is
    needed; the bot then asks the user to choose a category and learns it.
    """
    operation = (operation_type or "").upper()
    details_upper = (details or "").upper()
    merchant = normalize_merchant(details)
    search_text = f"{merchant} {details_upper}"

    if "ПОПОЛНЕНИЕ" in operation or "ЗАЧИСЛЕНИЕ" in operation:
        return "Income", merchant

    if "ПЕРЕВОД" in operation:
        return "Transfers", merchant

    if "СНЯТИЕ" in operation or "НАЛИЧ" in operation:
        return "Cash Withdrawal", merchant

    for key, category in BASE_MERCHANTS.items():
        if key in search_text:
            return category, merchant

    learned = load_merchants()
    for key, category in learned.items():
        if key in search_text:
            return category, merchant

    ai_category = ai_guess_category(merchant)
    if ai_category and ai_category != "Other":
        return ai_category, merchant

    return None, merchant
