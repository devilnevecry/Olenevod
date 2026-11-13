"""Pricing service: unit price by city, discounts, total."""

import uuid
from decimal import Decimal
from typing import Any

from olenevod.domain.exceptions import NotFound
from olenevod.infrastructure.repositories import CatalogRepository


class PricingService:
    """Price calculation by city. Pure logic on top of the repository."""

    def __init__(self, catalog_repo: CatalogRepository) -> None:
        self._repo = catalog_repo

    async def unit_price(self, city_id: uuid.UUID, variant_id: uuid.UUID) -> int:
        """Unit price of a variant in a city, in kopecks, or NotFound."""
        offer = await self._repo.get_city_offer(city_id, variant_id)
        if offer is None:
            raise NotFound("city_offer", f"city={city_id} variant={variant_id}")
        return int(offer.price_kop)

    async def line_total(
        self, city_id: uuid.UUID, variant_id: uuid.UUID, qty: int
    ) -> dict[str, Any]:
        """Total of a single line: price, old price, discount, amount."""
        offer = await self._repo.get_city_offer(city_id, variant_id)
        if offer is None:
            raise NotFound("city_offer", f"city={city_id} variant={variant_id}")
        unit = int(offer.price_kop)
        old_unit = int(offer.old_price_kop) if offer.old_price_kop is not None else None
        line = unit * qty
        old_line = old_unit * qty if old_unit is not None else None
        discount = (old_line - line) if (old_line is not None and old_line > line) else 0
        return {
            "variant_id": variant_id,
            "unit_price_kop": unit,
            "old_price_kop": old_unit,
            "qty": qty,
            "line_total_kop": line,
            "discount_kop": discount,
        }

    async def calculate_total(
        self, city_id: uuid.UUID, items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Cart total: subtotal, discount, total.

        items — list of {variant_id, qty}.
        """
        subtotal = 0
        discount = 0
        lines: list[dict[str, Any]] = []
        for item in items:
            variant_id = item["variant_id"]
            qty = int(item["qty"])
            line = await self.line_total(city_id, variant_id, qty)
            subtotal += line["line_total_kop"]
            discount += line["discount_kop"]
            lines.append(line)
        total = subtotal - discount
        return {
            "city_id": city_id,
            "subtotal_kop": subtotal,
            "discount_kop": discount,
            "total_kop": total,
            "currency": "RUB",
            "lines": lines,
        }

    def format_rub(self, kop: int) -> str:
        """Format kopecks as rubles for display."""
        rub = Decimal(kop) / 100
        return f"{rub:.2f} \u20bd"
