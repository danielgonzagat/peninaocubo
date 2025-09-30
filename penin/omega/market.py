from dataclasses import dataclass
from typing import List, Tuple


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
    def match(self, needs: List[Need], offers: List[Offer]) -> List[Tuple[Need, Offer, float]]:
        trades: List[Tuple[Need, Offer, float]] = []
        for n in needs:
            options = [o for o in offers if o.resource == n.resource and o.price <= n.max_price and o.qty > 0]
            if not options:
                continue
            o = min(options, key=lambda x: x.price)
            qty = min(n.qty, o.qty)
            if qty > 0:
                trades.append((n, o, qty))
                n.qty -= qty
                o.qty -= qty
        return trades

