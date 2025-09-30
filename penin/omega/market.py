"""
Cognitive Marketplace - Ω-Tokens Internal Economy
================================================

Implements internal marketplace for cognitive resources using Ω-tokens.
Supports needs/offers matching with price discovery.
"""

import time
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict


class ResourceType(Enum):
    """Types of cognitive resources"""
    CPU_TIME = "cpu_time"
    MEMORY = "memory"
    NEURONS = "neurons"
    ATTENTION = "attention"
    COMPUTE_SLOTS = "compute_slots"
    DATA_BANDWIDTH = "data_bandwidth"
    MODEL_CAPACITY = "model_capacity"


class TradeStatus(Enum):
    """Trade status"""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Need:
    """Resource need from an agent"""
    agent_id: str
    resource: ResourceType
    quantity: float
    max_price: float
    priority: int = 1  # Higher = more urgent
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if need is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class Offer:
    """Resource offer from an agent"""
    agent_id: str
    resource: ResourceType
    quantity: float
    price: float
    quality: float = 1.0  # Quality factor (0-1)
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if offer is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class Trade:
    """Executed trade"""
    trade_id: str
    need: Need
    offer: Offer
    quantity: float
    price: float
    timestamp: float = field(default_factory=time.time)
    status: TradeStatus = TradeStatus.EXECUTED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "need_agent": self.need.agent_id,
            "offer_agent": self.offer.agent_id,
            "resource": self.need.resource.value,
            "quantity": self.quantity,
            "price": self.price,
            "timestamp": self.timestamp,
            "status": self.status.value
        }


class AgentWallet:
    """Agent's Ω-token wallet"""
    
    def __init__(self, agent_id: str, initial_balance: float = 100.0):
        self.agent_id = agent_id
        self.balance = initial_balance
        self.transaction_history: List[Dict[str, Any]] = []
    
    def can_afford(self, amount: float) -> bool:
        """Check if agent can afford amount"""
        return self.balance >= amount
    
    def spend(self, amount: float, description: str = "") -> bool:
        """Spend tokens"""
        if not self.can_afford(amount):
            return False
        
        self.balance -= amount
        self.transaction_history.append({
            "type": "spend",
            "amount": amount,
            "balance_after": self.balance,
            "description": description,
            "timestamp": time.time()
        })
        return True
    
    def receive(self, amount: float, description: str = "") -> None:
        """Receive tokens"""
        self.balance += amount
        self.transaction_history.append({
            "type": "receive",
            "amount": amount,
            "balance_after": self.balance,
            "description": description,
            "timestamp": time.time()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get wallet statistics"""
        return {
            "agent_id": self.agent_id,
            "balance": self.balance,
            "transaction_count": len(self.transaction_history),
            "recent_transactions": self.transaction_history[-5:] if self.transaction_history else []
        }


class InternalMarket:
    """Internal cognitive marketplace"""
    
    def __init__(self):
        self.needs: List[Need] = []
        self.offers: List[Offer] = []
        self.trades: List[Trade] = []
        self.wallets: Dict[str, AgentWallet] = {}
        self.price_history: Dict[ResourceType, List[Tuple[float, float]]] = defaultdict(list)  # (price, timestamp)
        self.trade_counter = 0
    
    def create_wallet(self, agent_id: str, initial_balance: float = 100.0) -> AgentWallet:
        """Create wallet for agent"""
        wallet = AgentWallet(agent_id, initial_balance)
        self.wallets[agent_id] = wallet
        return wallet
    
    def get_wallet(self, agent_id: str) -> Optional[AgentWallet]:
        """Get agent's wallet"""
        return self.wallets.get(agent_id)
    
    def add_need(self, need: Need) -> bool:
        """Add resource need to market"""
        # Check if agent has wallet
        if need.agent_id not in self.wallets:
            self.create_wallet(need.agent_id)
        
        # Check if agent can afford
        wallet = self.wallets[need.agent_id]
        total_cost = need.quantity * need.max_price
        if not wallet.can_afford(total_cost):
            return False
        
        self.needs.append(need)
        return True
    
    def add_offer(self, offer: Offer) -> bool:
        """Add resource offer to market"""
        # Check if agent has wallet
        if offer.agent_id not in self.wallets:
            self.create_wallet(offer.agent_id)
        
        self.offers.append(offer)
        return True
    
    def match(self, needs: List[Need], offers: List[Offer]) -> List[Trade]:
        """
        Match needs with offers
        
        Args:
            needs: List of needs
            offers: List of offers
            
        Returns:
            List of executed trades
        """
        trades = []
        
        # Sort needs by priority (higher first)
        sorted_needs = sorted(needs, key=lambda n: n.priority, reverse=True)
        
        for need in sorted_needs:
            if need.is_expired():
                continue
            
            # Find compatible offers
            compatible_offers = [
                o for o in offers 
                if (o.resource == need.resource and 
                    o.price <= need.max_price and 
                    o.quantity > 0 and
                    not o.is_expired())
            ]
            
            if not compatible_offers:
                continue
            
            # Sort by price (lowest first)
            compatible_offers.sort(key=lambda o: o.price)
            
            remaining_quantity = need.quantity
            
            for offer in compatible_offers:
                if remaining_quantity <= 0:
                    break
                
                # Determine trade quantity
                trade_quantity = min(remaining_quantity, offer.quantity)
                trade_price = offer.price
                
                # Create trade
                trade_id = f"trade_{self.trade_counter:06d}"
                self.trade_counter += 1
                
                trade = Trade(
                    trade_id=trade_id,
                    need=need,
                    offer=offer,
                    quantity=trade_quantity,
                    price=trade_price
                )
                
                trades.append(trade)
                
                # Update quantities
                remaining_quantity -= trade_quantity
                offer.quantity -= trade_quantity
                
                # Record price
                self.price_history[need.resource].append((trade_price, time.time()))
        
        return trades
    
    def execute_trades(self, trades: List[Trade]) -> List[Trade]:
        """Execute trades and update wallets"""
        executed_trades = []
        
        for trade in trades:
            need_wallet = self.wallets.get(trade.need.agent_id)
            offer_wallet = self.wallets.get(trade.offer.agent_id)
            
            if not need_wallet or not offer_wallet:
                trade.status = TradeStatus.FAILED
                continue
            
            total_cost = trade.quantity * trade.price
            
            # Check if need agent can afford
            if not need_wallet.can_afford(total_cost):
                trade.status = TradeStatus.FAILED
                continue
            
            # Execute trade
            need_wallet.spend(total_cost, f"Trade {trade.trade_id}")
            offer_wallet.receive(total_cost, f"Trade {trade.trade_id}")
            
            trade.status = TradeStatus.EXECUTED
            executed_trades.append(trade)
            self.trades.append(trade)
        
        return executed_trades
    
    def process_market(self) -> Dict[str, Any]:
        """Process market and execute trades"""
        # Clean expired needs and offers
        self.needs = [n for n in self.needs if not n.is_expired()]
        self.offers = [o for o in self.offers if not o.is_expired()]
        
        # Match and execute trades
        trades = self.match(self.needs, self.offers)
        executed_trades = self.execute_trades(trades)
        
        # Remove fulfilled needs and empty offers
        self.needs = [n for n in self.needs if n.quantity > 0]
        self.offers = [o for o in self.offers if o.quantity > 0]
        
        return {
            "trades_executed": len(executed_trades),
            "trades": [t.to_dict() for t in executed_trades],
            "remaining_needs": len(self.needs),
            "remaining_offers": len(self.offers)
        }
    
    def get_market_price(self, resource: ResourceType, window_s: float = 300.0) -> Optional[float]:
        """Get current market price for resource"""
        cutoff_time = time.time() - window_s
        recent_prices = [
            price for price, timestamp in self.price_history[resource]
            if timestamp >= cutoff_time
        ]
        
        if not recent_prices:
            return None
        
        return sum(recent_prices) / len(recent_prices)
    
    def get_market_stats(self) -> Dict[str, Any]:
        """Get market statistics"""
        stats = {
            "total_needs": len(self.needs),
            "total_offers": len(self.offers),
            "total_trades": len(self.trades),
            "active_agents": len(self.wallets),
            "resource_prices": {}
        }
        
        # Get current prices for each resource
        for resource in ResourceType:
            price = self.get_market_price(resource)
            if price is not None:
                stats["resource_prices"][resource.value] = price
        
        # Agent balances
        agent_balances = {
            agent_id: wallet.balance 
            for agent_id, wallet in self.wallets.items()
        }
        stats["agent_balances"] = agent_balances
        
        return stats


class MarketOrchestrator:
    """Orchestrates market operations"""
    
    def __init__(self):
        self.market = InternalMarket()
        self.processing_interval = 10.0  # seconds
        self.last_process_time = 0
    
    def should_process(self) -> bool:
        """Check if market should be processed"""
        return time.time() - self.last_process_time > self.processing_interval
    
    def process_if_needed(self) -> Optional[Dict[str, Any]]:
        """Process market if needed"""
        if self.should_process():
            result = self.market.process_market()
            self.last_process_time = time.time()
            return result
        return None
    
    def create_agent(self, agent_id: str, initial_balance: float = 100.0) -> AgentWallet:
        """Create agent with wallet"""
        return self.market.create_wallet(agent_id, initial_balance)
    
    def request_resource(
        self,
        agent_id: str,
        resource: ResourceType,
        quantity: float,
        max_price: float,
        priority: int = 1,
        expires_in_s: Optional[float] = None
    ) -> bool:
        """Request resource"""
        expires_at = time.time() + expires_in_s if expires_in_s else None
        
        need = Need(
            agent_id=agent_id,
            resource=resource,
            quantity=quantity,
            max_price=max_price,
            priority=priority,
            expires_at=expires_at
        )
        
        return self.market.add_need(need)
    
    def offer_resource(
        self,
        agent_id: str,
        resource: ResourceType,
        quantity: float,
        price: float,
        quality: float = 1.0,
        expires_in_s: Optional[float] = None
    ) -> bool:
        """Offer resource"""
        expires_at = time.time() + expires_in_s if expires_in_s else None
        
        offer = Offer(
            agent_id=agent_id,
            resource=resource,
            quantity=quantity,
            price=price,
            quality=quality,
            expires_at=expires_at
        )
        
        return self.market.add_offer(offer)
    
    def get_agent_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent statistics"""
        wallet = self.market.get_wallet(agent_id)
        if not wallet:
            return None
        
        return wallet.get_stats()
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview"""
        return self.market.get_market_stats()


# Global market instance
_global_market: Optional[MarketOrchestrator] = None


def get_global_market() -> MarketOrchestrator:
    """Get global market instance"""
    global _global_market
    
    if _global_market is None:
        _global_market = MarketOrchestrator()
    
    return _global_market


def test_marketplace() -> Dict[str, Any]:
    """Test marketplace functionality"""
    market = get_global_market()
    
    # Create test agents
    agent_a = market.create_agent("agent-A", 200.0)
    agent_b = market.create_agent("agent-B", 150.0)
    agent_c = market.create_agent("agent-C", 100.0)
    
    # Agent A needs CPU time
    market.request_resource("agent-A", ResourceType.CPU_TIME, 10.0, 5.0, priority=2)
    
    # Agent B offers CPU time
    market.offer_resource("agent-B", ResourceType.CPU_TIME, 15.0, 4.0)
    
    # Agent C needs memory
    market.request_resource("agent-C", ResourceType.MEMORY, 5.0, 3.0, priority=1)
    
    # Agent A offers memory
    market.offer_resource("agent-A", ResourceType.MEMORY, 8.0, 2.5)
    
    # Process market
    result = market.process_market()
    
    # Get stats
    stats = market.get_market_overview()
    
    return {
        "processing_result": result,
        "market_stats": stats,
        "agent_stats": {
            "agent-A": market.get_agent_stats("agent-A"),
            "agent-B": market.get_agent_stats("agent-B"),
            "agent-C": market.get_agent_stats("agent-C")
        }
    }