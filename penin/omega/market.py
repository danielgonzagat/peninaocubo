"""
Cognitive Marketplace - Internal Resource Allocation
=====================================================

Implements internal marketplace for cognitive resources (CPU time, memory, tokens).
Uses simple matching algorithm with price discovery.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
import time


class ResourceType(Enum):
    """Types of cognitive resources"""
    CPU_TIME = "cpu_time"
    MEMORY = "memory"
    TOKENS = "tokens"
    NEURONS = "neurons"
    BANDWIDTH = "bandwidth"


@dataclass
class Need:
    """Resource need from an agent"""
    agent: str
    resource: str
    qty: float
    max_price: float
    priority: int = 5  # 1-10, higher is more important
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class Offer:
    """Resource offer from an agent"""
    agent: str
    resource: str
    qty: float
    price: float
    min_qty: float = 0.0  # Minimum quantity to sell
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class Trade:
    """Executed trade record"""
    need: Need
    offer: Offer
    qty: float
    price: float
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "buyer": self.need.agent,
            "seller": self.offer.agent,
            "resource": self.need.resource,
            "qty": self.qty,
            "price": self.price,
            "total_cost": self.qty * self.price,
            "timestamp": self.timestamp
        }


class InternalMarket:
    """Simple internal market with price discovery"""
    
    def __init__(self):
        self.trade_history: List[Trade] = []
        self.price_history: Dict[str, List[float]] = {}
        
    def match(self, needs: List[Need], offers: List[Offer]) -> List[Trade]:
        """
        Match needs with offers using simple greedy algorithm.
        
        Args:
            needs: List of resource needs
            offers: List of resource offers
        
        Returns:
            List of executed trades
        """
        trades = []
        
        # Sort needs by priority (high to low) then by max_price (high to low)
        needs = sorted(needs, key=lambda n: (-n.priority, -n.max_price))
        
        # Process each need
        for need in needs:
            if need.qty <= 0:
                continue
                
            # Find matching offers
            matching_offers = [
                o for o in offers
                if o.resource == need.resource
                and o.price <= need.max_price
                and o.qty > 0
            ]
            
            if not matching_offers:
                continue
            
            # Sort offers by price (low to high)
            matching_offers = sorted(matching_offers, key=lambda o: o.price)
            
            # Execute trades with best offers first
            for offer in matching_offers:
                if need.qty <= 0:
                    break
                    
                # Calculate trade quantity
                trade_qty = min(need.qty, offer.qty)
                
                # Check minimum quantity constraint
                if trade_qty < offer.min_qty:
                    continue
                
                # Execute trade
                trade = Trade(
                    need=need,
                    offer=offer,
                    qty=trade_qty,
                    price=offer.price
                )
                trades.append(trade)
                
                # Update quantities
                need.qty -= trade_qty
                offer.qty -= trade_qty
                
                # Record price for history
                if need.resource not in self.price_history:
                    self.price_history[need.resource] = []
                self.price_history[need.resource].append(offer.price)
        
        # Store trades in history
        self.trade_history.extend(trades)
        
        # Keep history bounded
        if len(self.trade_history) > 10000:
            self.trade_history = self.trade_history[-5000:]
        
        return trades
    
    def get_market_price(self, resource: str, window: int = 10) -> Optional[float]:
        """
        Get recent average price for a resource.
        
        Args:
            resource: Resource type
            window: Number of recent trades to average
        
        Returns:
            Average price or None if no history
        """
        if resource not in self.price_history:
            return None
            
        prices = self.price_history[resource][-window:]
        if not prices:
            return None
            
        return sum(prices) / len(prices)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get market statistics"""
        total_volume = sum(t.qty * t.price for t in self.trade_history)
        
        resource_volumes = {}
        for trade in self.trade_history:
            if trade.need.resource not in resource_volumes:
                resource_volumes[trade.need.resource] = 0
            resource_volumes[trade.need.resource] += trade.qty * trade.price
        
        return {
            "total_trades": len(self.trade_history),
            "total_volume": total_volume,
            "resource_volumes": resource_volumes,
            "avg_prices": {
                r: self.get_market_price(r)
                for r in self.price_history.keys()
            }
        }


class MarketMaker:
    """
    Automated market maker for providing liquidity.
    Sets prices based on supply/demand dynamics.
    """
    
    def __init__(self, base_prices: Dict[str, float] = None):
        self.base_prices = base_prices or {
            ResourceType.CPU_TIME.value: 1.0,
            ResourceType.MEMORY.value: 0.5,
            ResourceType.TOKENS.value: 0.1,
            ResourceType.NEURONS.value: 2.0,
            ResourceType.BANDWIDTH.value: 0.3,
        }
        self.price_adjustments = {r: 1.0 for r in self.base_prices}
        self.inventory = {r: 100.0 for r in self.base_prices}  # Initial inventory
        
    def update_prices(self, trades: List[Trade]):
        """Update prices based on recent trades"""
        # Count buy/sell pressure for each resource
        buy_pressure = {}
        sell_pressure = {}
        
        for trade in trades:
            resource = trade.need.resource
            if resource not in buy_pressure:
                buy_pressure[resource] = 0
                sell_pressure[resource] = 0
            
            buy_pressure[resource] += trade.qty
            sell_pressure[resource] += trade.qty
        
        # Adjust prices based on pressure
        for resource in self.base_prices:
            if resource in buy_pressure:
                # More buying than selling -> increase price
                ratio = buy_pressure[resource] / max(sell_pressure[resource], 1.0)
                adjustment = 1.0 + 0.1 * (ratio - 1.0)  # 10% adjustment per unit imbalance
                adjustment = max(0.5, min(2.0, adjustment))  # Cap adjustments
                self.price_adjustments[resource] *= adjustment
                
                # Keep adjustments bounded
                self.price_adjustments[resource] = max(0.1, min(10.0, self.price_adjustments[resource]))
    
    def get_price(self, resource: str) -> float:
        """Get current price for a resource"""
        base = self.base_prices.get(resource, 1.0)
        adjustment = self.price_adjustments.get(resource, 1.0)
        return base * adjustment
    
    def create_offers(self, resources: List[str] = None) -> List[Offer]:
        """Create market maker offers for liquidity"""
        if resources is None:
            resources = list(self.base_prices.keys())
        
        offers = []
        for resource in resources:
            if self.inventory.get(resource, 0) > 0:
                offers.append(Offer(
                    agent="market_maker",
                    resource=resource,
                    qty=min(10.0, self.inventory[resource]),
                    price=self.get_price(resource),
                    min_qty=0.1
                ))
        
        return offers
    
    def restock(self, resource: str, qty: float):
        """Restock inventory"""
        if resource not in self.inventory:
            self.inventory[resource] = 0
        self.inventory[resource] += qty


class CognitiveMarketplace:
    """High-level marketplace orchestrator"""
    
    def __init__(self):
        self.market = InternalMarket()
        self.maker = MarketMaker()
        self.pending_needs: List[Need] = []
        self.pending_offers: List[Offer] = []
        
    def submit_need(self, need: Need):
        """Submit a resource need"""
        self.pending_needs.append(need)
        
    def submit_offer(self, offer: Offer):
        """Submit a resource offer"""
        self.pending_offers.append(offer)
        
    def execute_round(self) -> Dict[str, Any]:
        """Execute a trading round"""
        # Add market maker offers for liquidity
        maker_offers = self.maker.create_offers()
        all_offers = self.pending_offers + maker_offers
        
        # Execute trades
        trades = self.market.match(self.pending_needs, all_offers)
        
        # Update market maker prices
        self.maker.update_prices(trades)
        
        # Clear pending orders
        self.pending_needs = [n for n in self.pending_needs if n.qty > 0]
        self.pending_offers = [o for o in self.pending_offers if o.qty > 0]
        
        return {
            "trades": [t.to_dict() for t in trades],
            "unfilled_needs": len(self.pending_needs),
            "remaining_offers": len(self.pending_offers),
            "market_stats": self.market.get_stats()
        }
    
    def get_price_quote(self, resource: str) -> float:
        """Get current price quote for a resource"""
        market_price = self.market.get_market_price(resource)
        if market_price:
            return market_price
        return self.maker.get_price(resource)