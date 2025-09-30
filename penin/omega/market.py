"""
Marketplace Cognitivo - Ω-tokens Internos
==========================================

Matching simples de necessidades e ofertas (recursos cognitivos).
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Need:
    """Necessidade de recurso"""
    agent: str
    resource: str
    qty: float
    max_price: float


@dataclass
class Offer:
    """Oferta de recurso"""
    agent: str
    resource: str
    qty: float
    price: float


class InternalMarket:
    """Marketplace interno de recursos cognitivos"""
    
    def match(self, needs: List[Need], offers: List[Offer]) -> List[Tuple[Need, Offer, float]]:
        """
        Faz matching entre necessidades e ofertas.
        
        Args:
            needs: Lista de necessidades
            offers: Lista de ofertas
            
        Returns:
            Lista de trades (need, offer, quantidade)
        """
        trades = []
        
        for n in needs:
            # Encontrar ofertas compatíveis
            options = [
                o for o in offers
                if o.resource == n.resource 
                and o.price <= n.max_price 
                and o.qty > 0
            ]
            
            if not options:
                continue
            
            # Escolher melhor preço
            o = min(options, key=lambda x: x.price)
            
            # Calcular quantidade do trade
            qty = min(n.qty, o.qty)
            
            if qty > 0:
                trades.append((n, o, qty))
                n.qty -= qty
                o.qty -= qty
        
        return trades
    
    def get_market_price(self, resource: str, offers: List[Offer]) -> float:
        """
        Obtém preço de mercado para um recurso.
        
        Args:
            resource: Nome do recurso
            offers: Lista de ofertas
            
        Returns:
            Preço médio ponderado
        """
        relevant = [o for o in offers if o.resource == resource and o.qty > 0]
        
        if not relevant:
            return 0.0
        
        total_qty = sum(o.qty for o in relevant)
        weighted_sum = sum(o.price * o.qty for o in relevant)
        
        return weighted_sum / total_qty if total_qty > 0 else 0.0