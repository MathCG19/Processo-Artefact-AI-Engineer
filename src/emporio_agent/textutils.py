"""Small text helpers for accent-insensitive, typo-tolerant matching in Portuguese."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

# Words that carry no signal for product lookup ("quanto custa o violão da yamaha?").
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "e", "ou", "de", "da", "do", "das", "dos",
    "em", "no", "na", "nos", "nas", "para", "pra", "pro", "com", "por", "que", "qual", "quais",
    "tem", "voces", "vcs", "me", "meu", "minha", "modelo", "produto", "instrumento", "the", "of",
}


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def normalize(text: object) -> str:
    """Lowercase, remove accents and punctuation: 'Violão Elétrico' -> 'violao eletrico'."""
    text = strip_accents(str(text)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def stem(token: str) -> str:
    """Very light Portuguese plural stemming: violões->violao, guitarras->guitarra."""
    if len(token) <= 3 or token.isdigit():
        return token
    if token.endswith(("oes", "aes")):
        return token[:-3] + "ao"
    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokens(text: object) -> list[str]:
    return [stem(t) for t in normalize(text).split() if t not in STOPWORDS]


def compact(text: object) -> str:
    """'GD-20' and 'gd 20' both become 'gd20' so model codes match regardless of spacing."""
    return normalize(text).replace(" ", "")


def fuzzy_equal(a: str, b: str, threshold: float = 0.84) -> bool:
    if a == b:
        return True
    if len(a) < 4 or len(b) < 4:
        return False
    return SequenceMatcher(None, a, b).ratio() >= threshold


def contains_phrase(haystack: str, phrase: str) -> bool:
    """Whole-word match on normalized text ('kala' does not match 'kalani')."""
    return f" {normalize(phrase)} " in f" {normalize(haystack)} "


def format_brl(value: float) -> str:
    """1234.5 -> 'R$ 1.234,50'"""
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def digits_only(text: object) -> str:
    return re.sub(r"\D", "", str(text))
