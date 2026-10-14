"""Dated public text pricing; never infer missing prices from model names."""
import re
from datetime import date

CHECKED = "2026-10-14"
SOURCES = {
    "openai": "https://developers.openai.com/api/docs/pricing",
    "anthropic": "https://platform.claude.com/docs/en/about-claude/pricing",
    "gemini": "https://ai.google.dev/gemini-api/docs/pricing",
    "groq": "https://console.groq.com/docs/models",
    "deepseek": "https://api-docs.deepseek.com/quick_start/pricing/",
}
# USD / million text tokens, standard uncached input and output, short context.
PRICES = {
    "openai": {"gpt-6-luna": (.10, .50), "gpt-6.1-sol": (2, 10), "gpt-6-astra": (10, 50)},
    "anthropic": {"claude-haiku-5-5": (.10, .50), "claude-sonnet-5-5": (2, 10),
                  "claude-opus-5-5": (4, 20), "claude-haiku-4-5": (1, 5), "claude-sonnet-4-6": (3, 15)},
    "gemini": {"gemini-2.5-flash-lite": (.10, .40), "gemini-2.5-flash": (.30, 2.50),
               "gemini-2.5-pro": (1.25, 10), "gemini-3.8-flash": (.75, 3.75)},
    "groq": {"openai/gpt-oss-20b": (.075, .30), "openai/gpt-oss-120b": (.15, .60), "qwen/qwen3.8-27b": (.80, 4)},
    "deepseek": {"deepseek-flash": (.30, 1.20), "deepseek-v4-pro": (1.32, 3.96)},
}


def enrich(provider: str, rows: list[dict], recommended: str) -> dict:
    fresh = 0 <= (date.today() - date.fromisoformat(CHECKED)).days <= 30
    for row in rows:
        row.pop("price", None)
        price = PRICES.get(provider, {}).get(row["id"]) if fresh else None
        if price:
            row["price"] = {"input": price[0], "output": price[1], "checked": CHECKED,
                            "source": SOURCES[provider]}
    priced = [row for row in rows if row.get("price")]
    cheapest = min(priced, key=lambda row: row["price"]["input"] * 5 + row["price"]["output"])["id"] if priced else None
    families = {"openai": ("astra", "sol", "luna"), "anthropic": ("fable", "mythos", "opus", "sonnet", "haiku"),
                "gemini": ("pro", "flash"), "deepseek": ("pro", "reasoner", "flash", "chat"),
                "groq": ("120b", "70b", "27b", "20b", "8b")}.get(provider, ())
    def capability(row):
        name = row["id"].lower()
        family = next((len(families) - i for i, token in enumerate(families) if token in name), 0)
        version = tuple(int(n) for n in re.findall(r"\d+", name)[:3])
        return family, version
    known = [row for row in rows if capability(row)[0]]
    smartest = max(known, key=capability)["id"] if known else None
    return {"recommended": recommended, "cheapest": cheapest, "smartest": smartest,
            "checked": CHECKED, "price_fresh": fresh,
            "note": "Termurah: estimasi 5.000 token input + 1.000 output, hanya model dengan harga tercatat. Tarif standar konteks pendek; DeepSeek memakai tarif peak. Gratis/kuota akun belum diperhitungkan. Paling pintar: saran keluarga model, bukan hasil benchmark. Harga dapat berubah."}
