"""
Cognitive Marketplace - Internal Ω-Tokens System
================================================

Implements internal marketplace for cognitive resources using Ω-tokens.
Enables resource allocation and trading between system components.
"""

import time
import uuid
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


class TradeStatus(Enum):
    """Status of a trade"""
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
    timestamp: float = field(default_factory=time.time)
    need_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Offer:
    """Resource offer from an agent"""
    agent_id: str
    resource: ResourceType
    quantity: float
    price: float
    quality: float = 1.0  # Quality factor (0-1)
    timestamp: float = field(default_factory=time.time)
    offer_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Trade:
    """Executed trade"""
    trade_id: str
    need: Need
    offer: Offer
    quantity: float
    price: float
    timestamp: float
    status: TradeStatus = TradeStatus.PENDING


@dataclass
class AgentWallet:
    """Agent's wallet with Ω-tokens"""
    agent_id: str
    balance: float = 100.0  # Starting balance
    reserved: float = 0.0   # Reserved for pending trades
    transaction_history: List[Dict[str, Any]] = field(default_factory=list)


class InternalMarket:
    """Internal cognitive marketplace"""
    
    def __init__(self, initial_token_supply: float = 10000.0):
        self.initial_supply = initial_token_supply
        self.total_supply = initial_token_supply
        self.circulating_supply = 0.0
        
        # Market state
        self.needs: List[Need] = []
        self.offers: List[Offer] = []
        self.trades: List[Trade] = []
        self.wallets: Dict[str, AgentWallet] = {}
        
        # Market statistics
        self.price_history: Dict[ResourceType, List[Tuple[float, float]]] = defaultdict(list)
        self.volume_history: List[Tuple[float, float]] = []  # (timestamp, volume)
        
        # Market parameters
        self.matching_algorithm = "price_time_priority"
        self.max_price_deviation = 0.1  # 10% max deviation from market price
        
    def create_agent(self, agent_id: str, initial_balance: float = 100.0) -> AgentWallet:
        """Create new agent with wallet"""
        wallet = AgentWallet(agent_id, initial_balance)
        self.wallets[agent_id] = wallet
        self.circulating_supply += initial_balance
        return wallet
    
    def add_need(self, need: Need) -> bool:
        """Add resource need to market"""
        # Check agent has sufficient balance
        wallet = self.wallets.get(need.agent_id)
        if not wallet:
            return False
        
        required_tokens = need.quantity * need.max_price
        if wallet.balance - wallet.reserved < required_tokens:
            return False
        
        # Reserve tokens
        wallet.reserved += required_tokens
        
        self.needs.append(need)
        return True
    
    def add_offer(self, offer: Offer) -> bool:
        """Add resource offer to market"""
        self.offers.append(offer)
        return True
    
    def match_trades(self) -> List[Trade]:
        """Match needs and offers to create trades"""
        executed_trades = []
        
        # Sort needs by priority and timestamp
        sorted_needs = sorted(self.needs, key=lambda n: (-n.priority, n.timestamp))
        
        for need in sorted_needs[:]:  # Copy to avoid modification during iteration
            # Find matching offers
            matching_offers = [
                o for o in self.offers
                if (o.resource == need.resource and 
                    o.price <= need.max_price and 
                    o.quantity > 0)
            ]
            
            if not matching_offers:
                continue
            
            # Sort by price (lowest first) and quality
            matching_offers.sort(key=lambda o: (o.price, -o.quality))
            
            best_offer = matching_offers[0]
            
            # Determine trade quantity
            trade_quantity = min(need.quantity, best_offer.quantity)
            trade_price = best_offer.price
            
            # Create trade
            trade = Trade(
                trade_id=str(uuid.uuid4()),
                need=need,
                offer=best_offer,
                quantity=trade_quantity,
                price=trade_price,
                timestamp=time.time()
            )
            
            # Execute trade
            if self._execute_trade(trade):
                executed_trades.append(trade)
                self.trades.append(trade)
                
                # Update quantities
                need.quantity -= trade_quantity
                best_offer.quantity -= trade_quantity
                
                # Remove fulfilled needs/offers
                if need.quantity <= 0:
                    self.needs.remove(need)
                    # Release reserved tokens
                    wallet = self.wallets[need.agent_id]
                    wallet.reserved -= need.max_price * trade_quantity
                
                if best_offer.quantity <= 0:
                    self.offers.remove(best_offer)
        
        return executed_trades
    
    def _execute_trade(self, trade: Trade) -> bool:
        """Execute a trade between agents"""
        need_wallet = self.wallets.get(trade.need.agent_id)
        offer_wallet = self.wallets.get(trade.offer.agent_id)
        
        if not need_wallet or not offer_wallet:
            return False
        
        trade_value = trade.quantity * trade.price
        
        # Check sufficient balance
        if need_wallet.balance < trade_value:
            return False
        
        # Transfer tokens
        need_wallet.balance -= trade_value
        offer_wallet.balance += trade_value
        
        # Record transactions
        need_wallet.transaction_history.append({
            "type": "purchase",
            "resource": trade.need.resource.value,
            "quantity": trade.quantity,
            "price": trade.price,
            "total": trade_value,
            "timestamp": trade.timestamp
        })
        
        offer_wallet.transaction_history.append({
            "type": "sale",
            "resource": trade.offer.resource.value,
            "quantity": trade.quantity,
            "price": trade.price,
            "total": trade_value,
            "timestamp": trade.timestamp
        })
        
        # Update market statistics
        self.price_history[trade.need.resource].append((trade.timestamp, trade.price))
        self.volume_history.append((trade.timestamp, trade_value))
        
        trade.status = TradeStatus.EXECUTED
        return True
    
    def get_market_price(self, resource: ResourceType, window_s: float = 300.0) -> Optional[float]:
        """Get current market price for resource"""
        cutoff_time = time.time() - window_s
        recent_prices = [
            price for timestamp, price in self.price_history[resource]
            if timestamp >= cutoff_time
        ]
        
        if not recent_prices:
            return None
        
        return sum(recent_prices) / len(recent_prices)
    
    def get_agent_balance(self, agent_id: str) -> Optional[float]:
        """Get agent's current balance"""
        wallet = self.wallets.get(agent_id)
        return wallet.balance if wallet else None
    
    def get_market_stats(self) -> Dict[str, Any]:
        """Get market statistics"""
        total_needs = sum(need.quantity for need in self.needs)
        total_offers = sum(offer.quantity for offer in self.offers)
        
        recent_volume = sum(
            volume for timestamp, volume in self.volume_history[-10:]
        )
        
        return {
            "total_needs": total_needs,
            "total_offers": total_offers,
            "active_trades": len([t for t in self.trades if t.status == TradeStatus.EXECUTED]),
            "recent_volume": recent_volume,
            "circulating_supply": self.circulating_supply,
            "active_agents": len(self.wallets),
            "resource_types": len(ResourceType)
        }
    
    def cleanup_expired(self, max_age_s: float = 3600.0):
        """Clean up expired needs and offers"""
        cutoff_time = time.time() - max_age_s
        
        # Remove expired needs
        expired_needs = [n for n in self.needs if n.timestamp < cutoff_time]
        for need in expired_needs:
            self.needs.remove(need)
            # Release reserved tokens
            wallet = self.wallets.get(need.agent_id)
            if wallet:
                wallet.reserved -= need.max_price * need.quantity
        
        # Remove expired offers
        expired_offers = [o for o in self.offers if o.timestamp < cutoff_time]
        for offer in expired_offers:
            self.offers.remove(offer)
        
        return len(expired_needs) + len(expired_offers)


class CognitiveScheduler:
    """Scheduler that uses marketplace for resource allocation"""
    
    def __init__(self, market: InternalMarket):
        self.market = market
        self.scheduler_id = "cognitive_scheduler"
        
        # Ensure scheduler has wallet
        if self.scheduler_id not in self.market.wallets:
            self.market.create_agent(self.scheduler_id, 1000.0)
    
    def allocate_resources(self, agent_requests: Dict[str, Dict[ResourceType, float]]) -> Dict[str, bool]:
        """Allocate resources to agents based on requests"""
        allocation_results = {}
        
        for agent_id, requests in agent_requests.items():
            success = True
            
            for resource_type, quantity in requests.items():
                # Create need
                market_price = self.market.get_market_price(resource_type) or 1.0
                need = Need(
                    agent_id=agent_id,
                    resource=resource_type,
                    quantity=quantity,
                    max_price=market_price * 1.1,  # 10% above market price
                    priority=2
                )
                
                if not self.market.add_need(need):
                    success = False
                    break
            
            allocation_results[agent_id] = success
        
        # Execute matching
        trades = self.market.match_trades()
        
        return allocation_results
    
    def get_allocation_status(self, agent_id: str) -> Dict[str, Any]:
        """Get allocation status for agent"""
        wallet = self.market.wallets.get(agent_id)
        if not wallet:
            return {"status": "no_wallet"}
        
        recent_trades = [
            t for t in wallet.transaction_history[-5:]
        ]
        
        return {
            "balance": wallet.balance,
            "reserved": wallet.reserved,
            "available": wallet.balance - wallet.reserved,
            "recent_trades": recent_trades
        }


# Integration with Life Equation
def integrate_marketplace_in_life_equation(
    life_verdict: Dict[str, Any],
    market: InternalMarket,
    agent_id: str = "life_equation_agent"
) -> Tuple[float, Dict[str, Any]]:
    """
    Integrate marketplace into Life Equation evaluation
    
    Args:
        life_verdict: Result from life_equation()
        market: Internal marketplace
        agent_id: Agent ID for marketplace
        
    Returns:
        (adjusted_alpha_eff, market_details)
    """
    if not life_verdict.get("ok", False):
        return 0.0, {"market_integration": "life_failed"}
    
    # Ensure agent exists in marketplace
    if agent_id not in market.wallets:
        market.create_agent(agent_id, 100.0)
    
    # Get current balance
    balance = market.get_agent_balance(agent_id)
    
    # Adjust alpha_eff based on available resources
    base_alpha_eff = life_verdict.get("alpha_eff", 0.0)
    
    # Resource availability factor (0.5 to 1.5)
    resource_factor = min(1.5, max(0.5, balance / 100.0))
    
    adjusted_alpha_eff = base_alpha_eff * resource_factor
    
    market_details = {
        "market_integration": "success",
        "agent_balance": balance,
        "resource_factor": resource_factor,
        "base_alpha_eff": base_alpha_eff,
        "adjusted_alpha_eff": adjusted_alpha_eff,
        "market_stats": market.get_market_stats()
    }
    
    return adjusted_alpha_eff, market_details


# Example usage
if __name__ == "__main__":
    # Create marketplace
    market = InternalMarket()
    
    # Create agents
    agent1 = market.create_agent("agent-1", 200.0)
    agent2 = market.create_agent("agent-2", 150.0)
    
    # Add needs and offers
    need = Need(
        agent_id="agent-1",
        resource=ResourceType.CPU_TIME,
        quantity=10.0,
        max_price=2.0
    )
    market.add_need(need)
    
    offer = Offer(
        agent_id="agent-2",
        resource=ResourceType.CPU_TIME,
        quantity=15.0,
        price=1.5
    )
    market.add_offer(offer)
    
    # Execute matching
    trades = market.match_trades()
    print(f"Executed {len(trades)} trades")
    
    # Check balances
    print(f"Agent-1 balance: {market.get_agent_balance('agent-1')}")
    print(f"Agent-2 balance: {market.get_agent_balance('agent-2')}")
    
    # Market stats
    stats = market.get_market_stats()
    print(f"Market stats: {stats}")