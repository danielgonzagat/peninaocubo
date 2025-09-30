"""
Marketplace Cognitivo - Ω-tokens Internos
=========================================

Sistema de marketplace interno para alocação de recursos cognitivos.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple


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
    """Marketplace cognitivo interno"""
    
    def match(self, needs: List[Need], offers: List[Offer]) -> List[Tuple[Need, Offer, float]]:
        """Matching simples de necessidades e ofertas"""
        trades = []
        
        for need in needs:
            # Encontrar ofertas compatíveis
            compatible_offers = [
                offer for offer in offers 
                if (offer.resource == need.resource and 
                    offer.price <= need.max_price and 
                    offer.qty > 0)
            ]
            
            if not compatible_offers:
                continue
            
            # Escolher oferta com melhor preço
            best_offer = min(compatible_offers, key=lambda x: x.price)
            
            # Calcular quantidade da transação
            trade_qty = min(need.qty, best_offer.qty)
            
            if trade_qty > 0:
                trades.append((need, best_offer, trade_qty))
                need.qty -= trade_qty
                best_offer.qty -= trade_qty
        
        return trades
    
    def get_market_price(self, resource: str, offers: List[Offer]) -> float:
        """Calcula preço de mercado para um recurso"""
        resource_offers = [o for o in offers if o.resource == resource and o.qty > 0]
        
        if not resource_offers:
            return 0.0
        
        # Preço médio ponderado por quantidade
        total_value = sum(o.price * o.qty for o in resource_offers)
        total_qty = sum(o.qty for o in resource_offers)
        
        return total_value / total_qty if total_qty > 0 else 0.0