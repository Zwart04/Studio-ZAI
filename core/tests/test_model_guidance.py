from datetime import date

from studiozai import model_guidance as guide


class CheckedDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 10, 14)


def test_cheapest_uses_known_prices_not_model_name(monkeypatch):
    monkeypatch.setattr(guide, "date", CheckedDate)
    rows = [{"id": name} for name in ["gpt-99-free-mini", "gpt-6-astra", "gpt-6-luna", "gpt-6.1-sol"]]
    result = guide.enrich("openai", rows, "gpt-6.1-sol")
    assert result["cheapest"] == "gpt-6-luna"
    assert result["smartest"] == "gpt-6-astra"
    assert result["recommended"] == "gpt-6.1-sol"
    assert "price" not in rows[0]
    assert rows[2]["price"]["input"] == .1


def test_unknown_endpoint_does_not_borrow_official_price(monkeypatch):
    monkeypatch.setattr(guide, "date", CheckedDate)
    rows = [{"id": "gpt-6-luna"}]
    result = guide.enrich("compatible", rows, rows[0]["id"])
    assert result["cheapest"] is None and result["smartest"] is None
    assert "price" not in rows[0]


def test_expired_prices_are_not_used_for_cheapest(monkeypatch):
    class Later(CheckedDate):
        @classmethod
        def today(cls):
            return cls(2027, 1, 1)
    monkeypatch.setattr(guide, "date", Later)
    result = guide.enrich("openai", [{"id": "gpt-6-luna"}], "gpt-6-luna")
    assert result["cheapest"] is None
    assert not result["price_fresh"]
