# penin/omega/market.py
"""
Marketplace Cognitivo - Ω-tokens Internos
=========================================

Implementa marketplace interno para alocação de recursos cognitivos
entre módulos do sistema PENIN-Ω. Usa tokens internos (Ω-tokens)
para orquestrar CPU time, "neurônios", slots de processamento, etc.

Características:
- Sistema de leilão simples para matching needs/offers
- Ω-tokens como moeda interna (não blockchain, apenas contabilidade)
- Recursos: cpu_time, memory_slots, neural_capacity, attention_slots
- Preços dinâmicos baseados em oferta/demanda
- Integração com scheduler e resource manager
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
from collections import defaultdict


class ResourceType(Enum):
    """Tipos de recursos no marketplace"""
    CPU_TIME = "cpu_time"           # Tempo de CPU (ms)
    MEMORY_SLOTS = "memory_slots"   # Slots de memória
    NEURAL_CAPACITY = "neural_capacity"  # Capacidade neural (unidades abstratas)
    ATTENTION_SLOTS = "attention_slots"  # Slots de atenção
    IO_BANDWIDTH = "io_bandwidth"   # Largura de banda I/O
    STORAGE_SPACE = "storage_space" # Espaço de armazenamento


class OrderType(Enum):
    """Tipos de ordem no marketplace"""
    BUY = "buy"    # Comprar recurso (need)
    SELL = "sell"  # Vender recurso (offer)


class OrderStatus(Enum):
    """Status de uma ordem"""
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Need:
    """Necessidade de recurso (ordem de compra)"""
    agent: str
    resource: ResourceType
    quantity: float
    max_price: float
    priority: float = 1.0
    timeout: float = 300.0  # 5 minutos
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "resource": self.resource.value,
            "quantity": self.quantity,
            "max_price": self.max_price,
            "priority": self.priority,
            "timeout": self.timeout,
            "created_at": self.created_at
        }
    
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout


@dataclass
class Offer:
    """Oferta de recurso (ordem de venda)"""
    agent: str
    resource: ResourceType
    quantity: float
    price: float
    quality: float = 1.0  # Qualidade do recurso (0-1)
    timeout: float = 300.0
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "resource": self.resource.value,
            "quantity": self.quantity,
            "price": self.price,
            "quality": self.quality,
            "timeout": self.timeout,
            "created_at": self.created_at
        }
    
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout


@dataclass
class Trade:
    """Transação executada"""
    buyer: str
    seller: str
    resource: ResourceType
    quantity: float
    price: float
    quality: float
    timestamp: float = field(default_factory=time.time)
    trade_id: str = field(default_factory=lambda: f"trade_{int(time.time() * 1000)}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "buyer": self.buyer,
            "seller": self.seller,
            "resource": self.resource.value,
            "quantity": self.quantity,
            "price": self.price,
            "quality": self.quality,
            "timestamp": self.timestamp
        }


@dataclass
class Account:
    """Conta de um agente no marketplace"""
    agent_id: str
    omega_tokens: float = 1000.0  # Saldo inicial
    resources: Dict[ResourceType, float] = field(default_factory=dict)
    trade_history: List[Trade] = field(default_factory=list)
    reputation: float = 1.0  # Reputação (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "omega_tokens": self.omega_tokens,
            "resources": {r.value: q for r, q in self.resources.items()},
            "trade_count": len(self.trade_history),
            "reputation": self.reputation
        }
    
    def get_resource(self, resource: ResourceType) -> float:
        return self.resources.get(resource, 0.0)
    
    def add_resource(self, resource: ResourceType, quantity: float) -> None:
        if resource not in self.resources:
            self.resources[resource] = 0.0
        self.resources[resource] += quantity
    
    def spend_tokens(self, amount: float) -> bool:
        if self.omega_tokens >= amount:
            self.omega_tokens -= amount
            return True
        return False
    
    def earn_tokens(self, amount: float) -> None:
        self.omega_tokens += amount


class InternalMarket:
    """
    Marketplace cognitivo interno
    
    Implementa leilão simples para matching de needs/offers
    """
    
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.pending_needs: List[Need] = []
        self.pending_offers: List[Offer] = []
        self.trade_history: List[Trade] = []
        self.price_history: Dict[ResourceType, List[Tuple[float, float]]] = defaultdict(list)  # (timestamp, price)
        
    def create_account(self, agent_id: str, initial_tokens: float = 1000.0) -> Account:
        """Cria conta para um agente"""
        if agent_id in self.accounts:
            return self.accounts[agent_id]
        
        account = Account(agent_id, initial_tokens)
        self.accounts[agent_id] = account
        return account
    
    def get_account(self, agent_id: str) -> Optional[Account]:
        """Obtém conta de um agente"""
        return self.accounts.get(agent_id)
    
    def submit_need(self, need: Need) -> bool:
        """Submete necessidade ao marketplace"""
        # Verificar se agente tem tokens suficientes
        account = self.get_account(need.agent)
        if not account:
            return False
        
        max_cost = need.quantity * need.max_price
        if account.omega_tokens < max_cost:
            return False
        
        self.pending_needs.append(need)
        return True
    
    def submit_offer(self, offer: Offer) -> bool:
        """Submete oferta ao marketplace"""
        # Verificar se agente tem recurso suficiente
        account = self.get_account(offer.agent)
        if not account:
            return False
        
        if account.get_resource(offer.resource) < offer.quantity:
            return False
        
        self.pending_offers.append(offer)
        return True
    
    def match_orders(self) -> List[Trade]:
        """
        Executa matching de ordens e retorna trades executados
        
        Algoritmo simples:
        1. Para cada need, encontra offers compatíveis
        2. Ordena offers por preço (menor primeiro)
        3. Executa trades até satisfazer need ou esgotar offers
        """
        trades = []
        
        # Remover ordens expiradas
        self._cleanup_expired_orders()
        
        # Processar needs por prioridade
        sorted_needs = sorted(self.pending_needs, key=lambda n: n.priority, reverse=True)
        
        for need in sorted_needs[:]:  # Cópia para permitir modificação
            if need.quantity <= 0:
                self.pending_needs.remove(need)
                continue
            
            # Encontrar offers compatíveis
            compatible_offers = [
                offer for offer in self.pending_offers
                if (offer.resource == need.resource and 
                    offer.price <= need.max_price and
                    offer.quantity > 0 and
                    offer.agent != need.agent)  # Não pode negociar consigo mesmo
            ]
            
            if not compatible_offers:
                continue
            
            # Ordenar por preço (menor primeiro) e qualidade (maior primeiro)
            compatible_offers.sort(key=lambda o: (o.price, -o.quality))
            
            # Executar trades
            for offer in compatible_offers:
                if need.quantity <= 0:
                    break
                
                # Quantidade a negociar
                trade_quantity = min(need.quantity, offer.quantity)
                
                # Executar trade
                trade = self._execute_trade(need, offer, trade_quantity)
                if trade:
                    trades.append(trade)
                    
                    # Atualizar quantidades
                    need.quantity -= trade_quantity
                    offer.quantity -= trade_quantity
                    
                    # Remover offer se esgotada
                    if offer.quantity <= 0:
                        self.pending_offers.remove(offer)
            
            # Remover need se satisfeita
            if need.quantity <= 0:
                self.pending_needs.remove(need)
        
        return trades
    
    def _execute_trade(self, need: Need, offer: Offer, quantity: float) -> Optional[Trade]:
        """Executa uma transação entre need e offer"""
        buyer_account = self.get_account(need.agent)
        seller_account = self.get_account(offer.agent)
        
        if not buyer_account or not seller_account:
            return None
        
        total_cost = quantity * offer.price
        
        # Verificar se buyer tem tokens suficientes
        if not buyer_account.spend_tokens(total_cost):
            return None
        
        # Verificar se seller tem recurso suficiente
        if seller_account.get_resource(offer.resource) < quantity:
            buyer_account.earn_tokens(total_cost)  # Reverter
            return None
        
        # Executar transferências
        seller_account.resources[offer.resource] -= quantity
        seller_account.earn_tokens(total_cost)
        
        buyer_account.add_resource(offer.resource, quantity)
        
        # Criar trade
        trade = Trade(
            buyer=need.agent,
            seller=offer.agent,
            resource=offer.resource,
            quantity=quantity,
            price=offer.price,
            quality=offer.quality
        )
        
        # Adicionar ao histórico
        self.trade_history.append(trade)
        buyer_account.trade_history.append(trade)
        seller_account.trade_history.append(trade)
        
        # Atualizar histórico de preços
        self.price_history[offer.resource].append((time.time(), offer.price))
        
        # Manter histórico limitado
        if len(self.price_history[offer.resource]) > 100:
            self.price_history[offer.resource].pop(0)
        
        return trade
    
    def _cleanup_expired_orders(self) -> None:
        """Remove ordens expiradas"""
        self.pending_needs = [n for n in self.pending_needs if not n.is_expired()]
        self.pending_offers = [o for o in self.pending_offers if not o.is_expired()]
    
    def get_market_price(self, resource: ResourceType, window_minutes: float = 60.0) -> Optional[float]:
        """Obtém preço médio de mercado para um recurso"""
        if resource not in self.price_history:
            return None
        
        cutoff_time = time.time() - (window_minutes * 60)
        recent_prices = [
            price for timestamp, price in self.price_history[resource]
            if timestamp >= cutoff_time
        ]
        
        if not recent_prices:
            return None
        
        return sum(recent_prices) / len(recent_prices)
    
    def get_market_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do marketplace"""
        stats = {
            "timestamp": time.time(),
            "accounts": len(self.accounts),
            "pending_needs": len(self.pending_needs),
            "pending_offers": len(self.pending_offers),
            "total_trades": len(self.trade_history),
            "resources": {}
        }
        
        # Estatísticas por recurso
        for resource in ResourceType:
            needs_count = sum(1 for n in self.pending_needs if n.resource == resource)
            offers_count = sum(1 for o in self.pending_offers if o.resource == resource)
            market_price = self.get_market_price(resource)
            
            stats["resources"][resource.value] = {
                "pending_needs": needs_count,
                "pending_offers": offers_count,
                "market_price": market_price,
                "liquidity": min(needs_count, offers_count)  # Liquidez aproximada
            }
        
        return stats
    
    def simulate_resource_allocation(self, agents: List[str], duration_minutes: float = 5.0) -> Dict[str, Any]:
        """
        Simula alocação de recursos por período determinado
        
        Args:
            agents: Lista de agentes participantes
            duration_minutes: Duração da simulação
            
        Returns:
            Relatório da simulação
        """
        # Criar contas se não existirem
        for agent in agents:
            if agent not in self.accounts:
                self.create_account(agent)
        
        # Distribuir recursos iniciais aleatoriamente
        import random
        for agent in agents:
            account = self.accounts[agent]
            for resource in ResourceType:
                initial_amount = random.uniform(10, 100)
                account.add_resource(resource, initial_amount)
        
        start_time = time.time()
        trades_executed = []
        
        # Simular atividade por duração especificada
        simulation_steps = int(duration_minutes * 12)  # 12 steps por minuto
        
        for step in range(simulation_steps):
            # Gerar needs e offers aleatórios
            for agent in agents:
                if random.random() < 0.3:  # 30% chance de gerar need
                    resource = random.choice(list(ResourceType))
                    quantity = random.uniform(1, 20)
                    max_price = random.uniform(0.5, 5.0)
                    
                    need = Need(agent, resource, quantity, max_price, priority=random.uniform(0.5, 2.0))
                    self.submit_need(need)
                
                if random.random() < 0.3:  # 30% chance de gerar offer
                    account = self.accounts[agent]
                    available_resources = [r for r, q in account.resources.items() if q > 1]
                    
                    if available_resources:
                        resource = random.choice(available_resources)
                        max_quantity = account.get_resource(resource)
                        quantity = random.uniform(1, min(20, max_quantity))
                        price = random.uniform(0.5, 5.0)
                        
                        offer = Offer(agent, resource, quantity, price, quality=random.uniform(0.7, 1.0))
                        self.submit_offer(offer)
            
            # Executar matching
            step_trades = self.match_orders()
            trades_executed.extend(step_trades)
            
            # Pequeno delay para simular tempo
            time.sleep(0.01)
        
        end_time = time.time()
        
        return {
            "simulation_duration": end_time - start_time,
            "agents": len(agents),
            "trades_executed": len(trades_executed),
            "final_market_stats": self.get_market_stats(),
            "agent_balances": {agent: self.accounts[agent].to_dict() for agent in agents}
        }


# Funções de conveniência
def quick_market_test() -> Dict[str, Any]:
    """Teste rápido do marketplace cognitivo"""
    market = InternalMarket()
    
    # Criar agentes
    agents = ["agent-A", "agent-B", "agent-C"]
    for agent in agents:
        market.create_account(agent, initial_tokens=1000.0)
    
    # Distribuir recursos iniciais
    market.accounts["agent-A"].add_resource(ResourceType.CPU_TIME, 100.0)
    market.accounts["agent-B"].add_resource(ResourceType.MEMORY_SLOTS, 50.0)
    market.accounts["agent-C"].add_resource(ResourceType.NEURAL_CAPACITY, 75.0)
    
    # Criar needs e offers
    need1 = Need("agent-B", ResourceType.CPU_TIME, 20.0, 2.0)
    offer1 = Offer("agent-A", ResourceType.CPU_TIME, 30.0, 1.5)
    
    need2 = Need("agent-C", ResourceType.MEMORY_SLOTS, 15.0, 3.0)
    offer2 = Offer("agent-B", ResourceType.MEMORY_SLOTS, 25.0, 2.5)
    
    # Submeter ordens
    market.submit_need(need1)
    market.submit_offer(offer1)
    market.submit_need(need2)
    market.submit_offer(offer2)
    
    # Executar matching
    trades = market.match_orders()
    
    # Obter estatísticas
    stats = market.get_market_stats()
    
    return {
        "agents_created": len(agents),
        "trades_executed": len(trades),
        "market_stats": stats,
        "trade_details": [trade.to_dict() for trade in trades]
    }


def validate_market_conservation() -> Dict[str, Any]:
    """
    Valida conservação de tokens e recursos no marketplace
    
    Testa se a soma total de tokens e recursos permanece constante
    """
    market = InternalMarket()
    
    # Criar agentes com valores conhecidos
    agents = ["test-A", "test-B"]
    initial_tokens = 500.0
    
    for agent in agents:
        market.create_account(agent, initial_tokens)
        market.accounts[agent].add_resource(ResourceType.CPU_TIME, 100.0)
    
    # Calcular totais iniciais
    initial_total_tokens = sum(acc.omega_tokens for acc in market.accounts.values())
    initial_total_cpu = sum(acc.get_resource(ResourceType.CPU_TIME) for acc in market.accounts.values())
    
    # Executar algumas transações
    need = Need("test-A", ResourceType.CPU_TIME, 30.0, 2.0)
    offer = Offer("test-B", ResourceType.CPU_TIME, 40.0, 1.8)
    
    market.submit_need(need)
    market.submit_offer(offer)
    trades = market.match_orders()
    
    # Calcular totais finais
    final_total_tokens = sum(acc.omega_tokens for acc in market.accounts.values())
    final_total_cpu = sum(acc.get_resource(ResourceType.CPU_TIME) for acc in market.accounts.values())
    
    # Verificar conservação
    tokens_conserved = abs(initial_total_tokens - final_total_tokens) < 1e-6
    cpu_conserved = abs(initial_total_cpu - final_total_cpu) < 1e-6
    
    return {
        "test": "market_conservation",
        "tokens_conserved": tokens_conserved,
        "cpu_conserved": cpu_conserved,
        "trades_executed": len(trades),
        "initial_totals": {"tokens": initial_total_tokens, "cpu": initial_total_cpu},
        "final_totals": {"tokens": final_total_tokens, "cpu": final_total_cpu},
        "passed": tokens_conserved and cpu_conserved
    }