"""
Cognitive Marketplace - Internal Resource Allocation
====================================================

Implements an internal marketplace where:
- Modules bid for resources (CPU time, "neurons", memory slots, etc.)
- Resources are allocated via simple matching (price-based)
- Ω-tokens serve as internal currency

This enables decentralized resource allocation without external dependencies.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum


class ResourceType(Enum):
    """Types of resources that can be traded"""
    CPU_TIME = "cpu_time"
    MEMORY_SLOT = "memory_slot"
    NEURON_ALLOCATION = "neuron_allocation"
    EVALUATION_SLOT = "evaluation_slot"
    INFERENCE_QUOTA = "inference_quota"


@dataclass
class Need:
    """A request to buy a resource"""
    agent: str
    resource: str
    qty: float
    max_price: float
    priority: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "resource": self.resource,
            "qty": self.qty,
            "max_price": self.max_price,
            "priority": self.priority
        }


@dataclass
class Offer:
    """An offer to sell a resource"""
    agent: str
    resource: str
    qty: float
    price: float
    quality: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "resource": self.resource,
            "qty": self.qty,
            "price": self.price,
            "quality": self.quality
        }


@dataclass
class Trade:
    """A completed trade"""
    buyer: str
    seller: str
    resource: str
    qty: float
    price: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "buyer": self.buyer,
            "seller": self.seller,
            "resource": self.resource,
            "qty": self.qty,
            "price": self.price,
            "timestamp": self.timestamp
        }


class InternalMarket:
    """
    Internal marketplace for resource allocation.
    
    Uses simple price-based matching:
    - For each need, find cheapest compatible offer
    - Execute trade if price acceptable
    - Update remaining quantities
    """
    
    def __init__(self):
        self.trade_history: List[Trade] = []
        self.agent_balances: Dict[str, float] = {}
        
        print("🛒 Internal Market initialized")
    
    def match(
        self,
        needs: List[Need],
        offers: List[Offer]
    ) -> List[Tuple[Need, Offer, float]]:
        """
        Match needs with offers.
        
        Args:
            needs: List of resource requests
            offers: List of resource offers
            
        Returns:
            List of (need, offer, qty) tuples for matched trades
        """
        trades = []
        
        # Sort needs by priority (high to low)
        sorted_needs = sorted(needs, key=lambda n: n.priority, reverse=True)
        
        for need in sorted_needs:
            # Find compatible offers
            compatible = [
                o for o in offers
                if o.resource == need.resource
                and o.price <= need.max_price
                and o.qty > 0
            ]
            
            if not compatible:
                continue
            
            # Choose cheapest offer
            best_offer = min(compatible, key=lambda o: o.price)
            
            # Execute trade
            qty = min(need.qty, best_offer.qty)
            if qty > 0:
                trades.append((need, best_offer, qty))
                need.qty -= qty
                best_offer.qty -= qty
        
        return trades
    
    def execute_trades(
        self,
        matches: List[Tuple[Need, Offer, float]]
    ) -> List[Trade]:
        """
        Execute matched trades and update balances.
        
        Args:
            matches: List of (need, offer, qty) tuples
            
        Returns:
            List of completed Trade objects
        """
        import time
        
        completed = []
        
        for need, offer, qty in matches:
            # Calculate cost
            cost = qty * offer.price
            
            # Update balances
            buyer = need.agent
            seller = offer.agent
            
            if buyer not in self.agent_balances:
                self.agent_balances[buyer] = 100.0  # Default starting balance
            
            if seller not in self.agent_balances:
                self.agent_balances[seller] = 100.0
            
            # Check if buyer has enough funds
            if self.agent_balances[buyer] < cost:
                print(f"⚠️  Trade failed: {buyer} insufficient funds")
                continue
            
            # Execute transfer
            self.agent_balances[buyer] -= cost
            self.agent_balances[seller] += cost
            
            # Record trade
            trade = Trade(
                buyer=buyer,
                seller=seller,
                resource=offer.resource,
                qty=qty,
                price=offer.price,
                timestamp=time.time()
            )
            
            self.trade_history.append(trade)
            completed.append(trade)
            
            print(f"✅ Trade: {buyer} bought {qty:.2f} {offer.resource} from {seller} @ {offer.price:.2f}")
        
        return completed
    
    def run_auction(
        self,
        needs: List[Need],
        offers: List[Offer]
    ) -> List[Trade]:
        """
        Run complete auction: match and execute.
        
        Args:
            needs: List of needs
            offers: List of offers
            
        Returns:
            List of completed trades
        """
        matches = self.match(needs, offers)
        return self.execute_trades(matches)
    
    def get_balance(self, agent: str) -> float:
        """Get agent's current balance"""
        return self.agent_balances.get(agent, 0.0)
    
    def set_balance(self, agent: str, balance: float) -> None:
        """Set agent's balance"""
        self.agent_balances[agent] = balance
    
    def get_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics"""
        if not self.trade_history:
            return {
                "total_trades": 0,
                "total_volume": 0.0,
                "agents": len(self.agent_balances)
            }
        
        total_volume = sum(t.qty * t.price for t in self.trade_history)
        
        # Resource breakdown
        resources = {}
        for trade in self.trade_history:
            if trade.resource not in resources:
                resources[trade.resource] = {"qty": 0.0, "value": 0.0}
            resources[trade.resource]["qty"] += trade.qty
            resources[trade.resource]["value"] += trade.qty * trade.price
        
        return {
            "total_trades": len(self.trade_history),
            "total_volume": total_volume,
            "agents": len(self.agent_balances),
            "resources": resources,
            "balances": dict(self.agent_balances)
        }


# Quick test function
def quick_market_test():
    """Quick test of marketplace functionality"""
    market = InternalMarket()
    
    # Set initial balances
    market.set_balance("explorer-1", 50.0)
    market.set_balance("core-0", 100.0)
    market.set_balance("validator-1", 75.0)
    
    # Create needs
    needs = [
        Need("explorer-1", "cpu_time", qty=10.0, max_price=2.0, priority=2.0),
        Need("core-0", "memory_slot", qty=5.0, max_price=3.0, priority=1.5),
        Need("validator-1", "inference_quota", qty=20.0, max_price=1.0, priority=1.0)
    ]
    
    # Create offers
    offers = [
        Offer("core-0", "cpu_time", qty=15.0, price=1.5, quality=0.9),
        Offer("validator-1", "memory_slot", qty=10.0, price=2.5, quality=1.0),
        Offer("explorer-1", "inference_quota", qty=25.0, price=0.8, quality=0.95)
    ]
    
    print("\n🛒 Running auction...")
    trades = market.run_auction(needs, offers)
    
    print(f"\n📊 Completed {len(trades)} trades")
    
    stats = market.get_stats()
    print(f"\n📈 Market stats:")
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    return market