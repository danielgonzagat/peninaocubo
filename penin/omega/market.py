"""
Cognitive Marketplace - Internal resource allocation with Ω-tokens
Implements matching between resource needs and offers
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional


@dataclass
class Need:
    """Resource need from an agent"""
    agent: str
    resource: str
    qty: float
    max_price: float
    priority: float = 1.0


@dataclass
class Offer:
    """Resource offer from an agent"""
    agent: str
    resource: str
    qty: float
    price: float
    quality: float = 1.0


@dataclass
class Trade:
    """Completed trade record"""
    buyer: str
    seller: str
    resource: str
    qty: float
    price: float
    timestamp: float = 0.0


class InternalMarket:
    """
    Internal cognitive marketplace for resource allocation
    Resources can be: CPU time, memory, attention slots, inference tokens, etc.
    """
    
    def __init__(self):
        self.trades_history: List[Trade] = []
        self.price_history: Dict[str, List[float]] = {}
    
    def match(self, needs: List[Need], offers: List[Offer]) -> List[Tuple[Need, Offer, float]]:
        """
        Match needs with offers using simple price-priority matching
        
        Parameters:
        -----------
        needs: List of resource needs
        offers: List of resource offers
        
        Returns:
        --------
        List of (need, offer, quantity) tuples for matched trades
        """
        trades = []
        
        # Sort needs by priority (descending) and max_price (descending)
        sorted_needs = sorted(needs, key=lambda n: (-n.priority, -n.max_price))
        
        # Sort offers by price (ascending) and quality (descending)
        sorted_offers = sorted(offers, key=lambda o: (o.price, -o.quality))
        
        # Match greedily
        for need in sorted_needs:
            # Find compatible offers
            compatible = [
                o for o in sorted_offers
                if o.resource == need.resource
                and o.price <= need.max_price
                and o.qty > 0
            ]
            
            if not compatible:
                continue
            
            # Take the best offer (already sorted by price/quality)
            offer = compatible[0]
            
            # Determine trade quantity
            qty = min(need.qty, offer.qty)
            
            if qty > 0:
                trades.append((need, offer, qty))
                need.qty -= qty
                offer.qty -= qty
                
                # Record trade
                trade = Trade(
                    buyer=need.agent,
                    seller=offer.agent,
                    resource=need.resource,
                    qty=qty,
                    price=offer.price
                )
                self.trades_history.append(trade)
                
                # Update price history
                if need.resource not in self.price_history:
                    self.price_history[need.resource] = []
                self.price_history[need.resource].append(offer.price)
        
        return trades
    
    def get_market_price(self, resource: str, window: int = 10) -> Optional[float]:
        """
        Get current market price for a resource
        
        Parameters:
        -----------
        resource: Resource name
        window: Number of recent trades to consider
        
        Returns:
        --------
        Average price from recent trades, or None if no history
        """
        if resource not in self.price_history:
            return None
        
        history = self.price_history[resource]
        if not history:
            return None
        
        recent = history[-window:] if len(history) > window else history
        return sum(recent) / len(recent)
    
    def compute_liquidity(self, resource: str) -> float:
        """
        Compute liquidity score for a resource (0=illiquid, 1=very liquid)
        
        Parameters:
        -----------
        resource: Resource name
        
        Returns:
        --------
        Liquidity score based on trade frequency
        """
        if resource not in self.price_history:
            return 0.0
        
        trade_count = len(self.price_history[resource])
        
        # Simple liquidity metric: saturates at 100 trades
        return min(1.0, trade_count / 100.0)
    
    def price_discovery(
        self,
        resource: str,
        base_price: float,
        demand_supply_ratio: float
    ) -> float:
        """
        Discover new price based on demand/supply dynamics
        
        Parameters:
        -----------
        resource: Resource name
        base_price: Base price for the resource
        demand_supply_ratio: Ratio of total demand to total supply
        
        Returns:
        --------
        Adjusted price based on market dynamics
        """
        # Get historical market price if available
        market_price = self.get_market_price(resource)
        
        if market_price is not None:
            # Blend with historical price
            base_price = 0.7 * base_price + 0.3 * market_price
        
        # Adjust based on demand/supply
        # High demand (ratio > 1) increases price
        # Low demand (ratio < 1) decreases price
        adjustment = 1.0 + 0.2 * (demand_supply_ratio - 1.0)
        adjustment = max(0.5, min(2.0, adjustment))  # Cap adjustment
        
        return base_price * adjustment
    
    def clear_market(
        self,
        needs: List[Need],
        offers: List[Offer],
        iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Run multiple rounds of market clearing with price discovery
        
        Parameters:
        -----------
        needs: Initial needs
        offers: Initial offers
        iterations: Number of clearing rounds
        
        Returns:
        --------
        Market clearing results with statistics
        """
        total_trades = []
        unmatched_needs = list(needs)
        unmatched_offers = list(offers)
        
        for round_num in range(iterations):
            # Match current needs and offers
            trades = self.match(unmatched_needs, unmatched_offers)
            total_trades.extend(trades)
            
            # Update unmatched lists
            unmatched_needs = [n for n in unmatched_needs if n.qty > 0]
            unmatched_offers = [o for o in unmatched_offers if o.qty > 0]
            
            # Price discovery for next round
            for resource in set(n.resource for n in unmatched_needs):
                demand = sum(n.qty for n in unmatched_needs if n.resource == resource)
                supply = sum(o.qty for o in unmatched_offers if o.resource == resource)
                
                if supply > 0:
                    ratio = demand / supply
                    base_price = self.get_market_price(resource) or 1.0
                    new_price = self.price_discovery(resource, base_price, ratio)
                    
                    # Update offer prices for next round
                    for offer in unmatched_offers:
                        if offer.resource == resource:
                            offer.price = new_price
        
        # Compute statistics
        total_volume = sum(qty for _, _, qty in total_trades)
        total_value = sum(offer.price * qty for _, offer, qty in total_trades)
        fulfillment_rate = 1.0 - (len(unmatched_needs) / len(needs)) if needs else 1.0
        
        return {
            "trades": total_trades,
            "unmatched_needs": unmatched_needs,
            "unmatched_offers": unmatched_offers,
            "total_volume": total_volume,
            "total_value": total_value,
            "fulfillment_rate": fulfillment_rate,
            "rounds": iterations
        }


def quick_test():
    """Quick test of marketplace"""
    market = InternalMarket()
    
    # Create some needs
    needs = [
        Need("agent-1", "cpu", 10.0, 2.0, priority=2.0),
        Need("agent-2", "memory", 5.0, 1.5, priority=1.0),
        Need("agent-3", "cpu", 8.0, 1.8, priority=1.5),
    ]
    
    # Create some offers
    offers = [
        Offer("provider-1", "cpu", 15.0, 1.5, quality=0.9),
        Offer("provider-2", "memory", 10.0, 1.0, quality=0.95),
        Offer("provider-3", "cpu", 5.0, 1.7, quality=0.85),
    ]
    
    # Run market clearing
    result = market.clear_market(needs, offers, iterations=2)
    
    return {
        "trades_count": len(result["trades"]),
        "total_volume": result["total_volume"],
        "fulfillment_rate": result["fulfillment_rate"],
        "cpu_price": market.get_market_price("cpu"),
        "memory_price": market.get_market_price("memory")
    }


if __name__ == "__main__":
    result = quick_test()
    print("Cognitive Marketplace Test:")
    print(f"  Trades executed: {result['trades_count']}")
    print(f"  Total volume: {result['total_volume']:.1f}")
    print(f"  Fulfillment rate: {result['fulfillment_rate']:.1%}")
    print(f"  CPU market price: {result['cpu_price']:.2f}" if result['cpu_price'] else "  CPU: no price history")
    print(f"  Memory market price: {result['memory_price']:.2f}" if result['memory_price'] else "  Memory: no price history")