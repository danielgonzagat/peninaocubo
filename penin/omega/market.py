from dataclasses import dataclass


@dataclass
class Need:
    agent: str
    resource: str
    qty: float
    max_price: float


@dataclass
class Offer:
    agent: str
    resource: str
    qty: float
    price: float


class InternalMarket:
    def match(
        self, needs: list[Need], offers: list[Offer]
    ) -> list[tuple[Need, Offer, float]]:
        trades: list[tuple[Need, Offer, float]] = []
        for n in needs:
            candidates = [
                o
                for o in offers
                if o.resource == n.resource and o.price <= n.max_price and o.qty > 0
            ]
            if not candidates:
                continue
            # Choose lowest price
            o = min(candidates, key=lambda x: x.price)
            qty = min(max(0.0, n.qty), max(0.0, o.qty))
            if qty > 0:
                trades.append((n, o, qty))
                n.qty -= qty
                o.qty -= qty
        return trades
