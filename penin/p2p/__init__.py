"""
PENIN P2P Protocol

Protocolo de Entanglement de Inteligência Neuromórfica (PENIN Protocol)
Permite comunicação P2P entre instâncias PENIN-Ω para troca de conhecimento e evolução colaborativa.

Baseado em libp2p para máxima flexibilidade e descentralização.
"""

from penin.p2p.node import PeninNode
from penin.p2p.protocol import MessageType, PeninProtocol

__all__ = [
    "PeninNode",
    "PeninProtocol",
    "MessageType",
]
