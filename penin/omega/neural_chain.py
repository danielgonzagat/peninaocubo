# penin/omega/neural_chain.py
"""
Blockchain Neural Leve - Sobre WORM
===================================

Implementa blockchain neural leve construído sobre o WORM ledger existente.
Adiciona encadeamento explícito de blocos cognitivos com HMAC local.

Características:
- Blocos encadeados com hash do bloco anterior
- HMAC-SHA256 para integridade (chave via PENIN_CHAIN_KEY)
- Snapshots de estado cognitivo por bloco
- Persistência em ~/.penin_omega/worm_ledger/neural_chain.jsonl
- Validação de cadeia e detecção de tampering
- Integração com WORM para auditoria completa
"""

import hmac
import hashlib
import time
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

try:
    import orjson
    JSON_LIB = orjson
    def json_dumps(obj): return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS).decode()
    def json_loads(s): return orjson.loads(s)
except ImportError:
    JSON_LIB = json
    def json_dumps(obj): return json.dumps(obj, sort_keys=True, ensure_ascii=False)
    def json_loads(s): return json.loads(s)


# Configuração
CHAIN_KEY = (os.getenv("PENIN_CHAIN_KEY") or "penin-dev-neural-key").encode()
ROOT = Path.home() / ".penin_omega" / "worm_ledger"
ROOT.mkdir(parents=True, exist_ok=True)
CHAIN_FILE = ROOT / "neural_chain.jsonl"


@dataclass
class CognitiveState:
    """Estado cognitivo para snapshot no bloco"""
    phi: float                    # CAOS⁺
    sr: float                     # Self-Reflection
    G: float                      # Coerência global
    alpha_eff: float              # Alpha efetivo da Equação de Vida
    life_verdict: bool            # Se Equação de Vida passou
    ethics_ok: bool               # Se Σ-Guard passou
    contractive: bool             # Se IR→IC passou
    exploration_factor: float     # Fator de exploração KRATOS
    swarm_nodes: int              # Número de nós ativos no swarm
    market_trades: int            # Número de trades no marketplace
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phi": self.phi,
            "sr": self.sr,
            "G": self.G,
            "alpha_eff": self.alpha_eff,
            "life_verdict": self.life_verdict,
            "ethics_ok": self.ethics_ok,
            "contractive": self.contractive,
            "exploration_factor": self.exploration_factor,
            "swarm_nodes": self.swarm_nodes,
            "market_trades": self.market_trades
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CognitiveState':
        return cls(**data)


@dataclass
class NeuralBlock:
    """Bloco na blockchain neural"""
    block_id: int
    timestamp: float
    prev_hash: str
    cognitive_state: CognitiveState
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "cognitive_state": self.cognitive_state.to_dict(),
            "metadata": self.metadata,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NeuralBlock':
        cognitive_state = CognitiveState.from_dict(data["cognitive_state"])
        return cls(
            block_id=data["block_id"],
            timestamp=data["timestamp"],
            prev_hash=data["prev_hash"],
            cognitive_state=cognitive_state,
            metadata=data.get("metadata", {}),
            hash=data.get("hash", "")
        )


def _hash_block(block: NeuralBlock) -> str:
    """Gera hash HMAC-SHA256 do bloco"""
    # Criar dict sem o hash para calcular
    block_data = block.to_dict()
    block_data.pop("hash", None)  # Remover hash se existir
    
    # Serializar de forma determinística
    raw_data = json_dumps(block_data).encode()
    
    # Calcular HMAC
    return hmac.new(CHAIN_KEY, raw_data, hashlib.sha256).hexdigest()


def _verify_block_hash(block: NeuralBlock) -> bool:
    """Verifica se o hash do bloco está correto"""
    expected_hash = _hash_block(block)
    return block.hash == expected_hash


def add_block(cognitive_state: CognitiveState, 
              prev_hash: Optional[str] = None,
              metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Adiciona novo bloco à blockchain neural
    
    Args:
        cognitive_state: Estado cognitivo atual
        prev_hash: Hash do bloco anterior (None para genesis)
        metadata: Metadados adicionais
        
    Returns:
        Hash do bloco criado
    """
    # Determinar ID do bloco
    if prev_hash is None:
        block_id = 0
        prev_hash = "GENESIS"
    else:
        # Contar blocos existentes
        block_id = count_blocks()
    
    # Criar bloco
    block = NeuralBlock(
        block_id=block_id,
        timestamp=time.time(),
        prev_hash=prev_hash,
        cognitive_state=cognitive_state,
        metadata=metadata or {}
    )
    
    # Calcular hash
    block.hash = _hash_block(block)
    
    # Persistir
    with CHAIN_FILE.open("ab") as f:
        f.write(json_dumps(block.to_dict()).encode() + b"\n")
    
    return block.hash


def get_latest_block() -> Optional[NeuralBlock]:
    """Obtém o último bloco da cadeia"""
    if not CHAIN_FILE.exists():
        return None
    
    try:
        with CHAIN_FILE.open("rb") as f:
            lines = f.readlines()
        
        if not lines:
            return None
        
        # Última linha
        last_line = lines[-1].decode().strip()
        if not last_line:
            return None
        
        block_data = json_loads(last_line)
        return NeuralBlock.from_dict(block_data)
    
    except Exception:
        return None


def get_block_by_id(block_id: int) -> Optional[NeuralBlock]:
    """Obtém bloco por ID"""
    if not CHAIN_FILE.exists():
        return None
    
    try:
        with CHAIN_FILE.open("rb") as f:
            for line in f:
                line = line.decode().strip()
                if not line:
                    continue
                
                block_data = json_loads(line)
                if block_data.get("block_id") == block_id:
                    return NeuralBlock.from_dict(block_data)
    
    except Exception:
        pass
    
    return None


def count_blocks() -> int:
    """Conta número de blocos na cadeia"""
    if not CHAIN_FILE.exists():
        return 0
    
    try:
        with CHAIN_FILE.open("rb") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def validate_chain() -> Dict[str, Any]:
    """
    Valida integridade da blockchain neural
    
    Verifica:
    - Hashes dos blocos
    - Encadeamento correto (prev_hash)
    - Sequência de IDs
    - Timestamps crescentes
    """
    validation = {
        "timestamp": time.time(),
        "total_blocks": 0,
        "valid_blocks": 0,
        "invalid_blocks": 0,
        "errors": [],
        "valid": True
    }
    
    if not CHAIN_FILE.exists():
        validation["errors"].append("Chain file does not exist")
        validation["valid"] = False
        return validation
    
    try:
        blocks = []
        with CHAIN_FILE.open("rb") as f:
            for line_num, line in enumerate(f, 1):
                line = line.decode().strip()
                if not line:
                    continue
                
                try:
                    block_data = json_loads(line)
                    block = NeuralBlock.from_dict(block_data)
                    blocks.append(block)
                except Exception as e:
                    validation["errors"].append(f"Line {line_num}: Invalid JSON - {e}")
                    validation["invalid_blocks"] += 1
        
        validation["total_blocks"] = len(blocks)
        
        # Validar cada bloco
        prev_block = None
        for i, block in enumerate(blocks):
            block_valid = True
            
            # Verificar hash do bloco
            if not _verify_block_hash(block):
                validation["errors"].append(f"Block {block.block_id}: Invalid hash")
                block_valid = False
            
            # Verificar encadeamento
            if i == 0:
                # Genesis block
                if block.prev_hash != "GENESIS":
                    validation["errors"].append(f"Block {block.block_id}: Invalid genesis prev_hash")
                    block_valid = False
                if block.block_id != 0:
                    validation["errors"].append(f"Block {block.block_id}: Genesis should have ID 0")
                    block_valid = False
            else:
                # Bloco regular
                if prev_block and block.prev_hash != prev_block.hash:
                    validation["errors"].append(f"Block {block.block_id}: Broken chain link")
                    block_valid = False
                
                if block.block_id != i:
                    validation["errors"].append(f"Block {block.block_id}: ID sequence broken")
                    block_valid = False
                
                if prev_block and block.timestamp <= prev_block.timestamp:
                    validation["errors"].append(f"Block {block.block_id}: Timestamp not increasing")
                    block_valid = False
            
            if block_valid:
                validation["valid_blocks"] += 1
            else:
                validation["invalid_blocks"] += 1
            
            prev_block = block
        
        # Determinar validade geral
        validation["valid"] = (validation["invalid_blocks"] == 0 and len(validation["errors"]) == 0)
    
    except Exception as e:
        validation["errors"].append(f"Validation error: {e}")
        validation["valid"] = False
    
    return validation


def get_chain_summary() -> Dict[str, Any]:
    """Retorna resumo da blockchain neural"""
    summary = {
        "timestamp": time.time(),
        "total_blocks": count_blocks(),
        "chain_file": str(CHAIN_FILE),
        "file_exists": CHAIN_FILE.exists(),
        "file_size_bytes": CHAIN_FILE.stat().st_size if CHAIN_FILE.exists() else 0
    }
    
    # Informações do último bloco
    latest = get_latest_block()
    if latest:
        summary["latest_block"] = {
            "block_id": latest.block_id,
            "timestamp": latest.timestamp,
            "hash": latest.hash[:16] + "...",  # Primeiros 16 chars
            "cognitive_state": latest.cognitive_state.to_dict()
        }
    else:
        summary["latest_block"] = None
    
    # Validação rápida
    validation = validate_chain()
    summary["validation"] = {
        "valid": validation["valid"],
        "error_count": len(validation["errors"])
    }
    
    return summary


def get_cognitive_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retorna histórico de estados cognitivos
    
    Args:
        limit: Número máximo de blocos a retornar
        
    Returns:
        Lista de estados cognitivos dos últimos blocos
    """
    if not CHAIN_FILE.exists():
        return []
    
    history = []
    
    try:
        with CHAIN_FILE.open("rb") as f:
            lines = f.readlines()
        
        # Pegar últimas linhas
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        for line in recent_lines:
            line = line.decode().strip()
            if not line:
                continue
            
            try:
                block_data = json_loads(line)
                block = NeuralBlock.from_dict(block_data)
                
                history.append({
                    "block_id": block.block_id,
                    "timestamp": block.timestamp,
                    "cognitive_state": block.cognitive_state.to_dict(),
                    "hash": block.hash[:16] + "..."
                })
            except Exception:
                continue
    
    except Exception:
        pass
    
    return history


class NeuralChainManager:
    """
    Gerenciador da blockchain neural
    
    Facilita operações de alto nível na cadeia
    """
    
    def __init__(self):
        self.last_block_hash = None
        self._update_last_hash()
    
    def _update_last_hash(self) -> None:
        """Atualiza hash do último bloco"""
        latest = get_latest_block()
        self.last_block_hash = latest.hash if latest else None
    
    def add_cognitive_snapshot(self, 
                              phi: float, sr: float, G: float, alpha_eff: float,
                              life_verdict: bool, ethics_ok: bool, contractive: bool,
                              exploration_factor: float = 1.0,
                              swarm_nodes: int = 0, market_trades: int = 0,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Adiciona snapshot do estado cognitivo atual
        
        Returns:
            Hash do bloco criado
        """
        cognitive_state = CognitiveState(
            phi=phi,
            sr=sr,
            G=G,
            alpha_eff=alpha_eff,
            life_verdict=life_verdict,
            ethics_ok=ethics_ok,
            contractive=contractive,
            exploration_factor=exploration_factor,
            swarm_nodes=swarm_nodes,
            market_trades=market_trades
        )
        
        block_hash = add_block(cognitive_state, self.last_block_hash, metadata)
        self.last_block_hash = block_hash
        
        return block_hash
    
    def get_cognitive_trend(self, metric: str, window: int = 5) -> Dict[str, Any]:
        """
        Analisa tendência de uma métrica cognitiva
        
        Args:
            metric: Nome da métrica (phi, sr, G, alpha_eff, etc.)
            window: Número de blocos para análise
            
        Returns:
            Análise de tendência
        """
        history = get_cognitive_history(window)
        
        if len(history) < 2:
            return {"trend": "insufficient_data", "values": []}
        
        values = []
        for entry in history:
            if metric in entry["cognitive_state"]:
                values.append(entry["cognitive_state"][metric])
        
        if len(values) < 2:
            return {"trend": "no_data", "values": values}
        
        # Análise simples de tendência
        recent_avg = sum(values[-3:]) / len(values[-3:]) if len(values) >= 3 else values[-1]
        earlier_avg = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else values[0]
        
        if recent_avg > earlier_avg * 1.05:
            trend = "increasing"
        elif recent_avg < earlier_avg * 0.95:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "values": values,
            "recent_avg": recent_avg,
            "earlier_avg": earlier_avg,
            "change_ratio": recent_avg / max(1e-9, earlier_avg)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde da blockchain neural"""
        validation = validate_chain()
        summary = get_chain_summary()
        
        # Determinar saúde geral
        if validation["valid"] and summary["total_blocks"] > 0:
            health_status = "healthy"
        elif validation["valid"] and summary["total_blocks"] == 0:
            health_status = "empty"
        else:
            health_status = "corrupted"
        
        return {
            "status": health_status,
            "total_blocks": summary["total_blocks"],
            "validation_errors": len(validation["errors"]),
            "file_size_mb": summary["file_size_bytes"] / (1024 * 1024),
            "latest_block_age_minutes": (
                (time.time() - summary["latest_block"]["timestamp"]) / 60
                if summary["latest_block"] else None
            )
        }


# Funções de conveniência
def quick_neural_chain_test() -> Dict[str, Any]:
    """Teste rápido da blockchain neural"""
    manager = NeuralChainManager()
    
    # Adicionar alguns blocos de teste
    test_blocks = []
    
    for i in range(3):
        block_hash = manager.add_cognitive_snapshot(
            phi=0.7 + i * 0.1,
            sr=0.8 + i * 0.05,
            G=0.85 + i * 0.02,
            alpha_eff=0.001 + i * 0.0005,
            life_verdict=True,
            ethics_ok=True,
            contractive=True,
            exploration_factor=1.5 + i * 0.2,
            swarm_nodes=3 + i,
            market_trades=i * 2,
            metadata={"test_block": i}
        )
        test_blocks.append(block_hash)
        time.sleep(0.01)  # Pequeno delay para timestamps diferentes
    
    # Obter resumo
    summary = get_chain_summary()
    
    # Validar cadeia
    validation = validate_chain()
    
    # Analisar tendência
    phi_trend = manager.get_cognitive_trend("phi")
    
    return {
        "blocks_added": len(test_blocks),
        "chain_summary": summary,
        "validation": validation,
        "phi_trend": phi_trend,
        "health": manager.health_check()
    }


def validate_neural_chain_integrity() -> Dict[str, Any]:
    """
    Valida integridade da blockchain neural
    
    Testa detecção de tampering e validação de hashes
    """
    # Limpar cadeia existente para teste limpo
    if CHAIN_FILE.exists():
        backup_file = CHAIN_FILE.with_suffix(".backup")
        CHAIN_FILE.rename(backup_file)
    
    try:
        manager = NeuralChainManager()
        
        # Adicionar bloco válido
        hash1 = manager.add_cognitive_snapshot(
            phi=0.8, sr=0.9, G=0.85, alpha_eff=0.002,
            life_verdict=True, ethics_ok=True, contractive=True
        )
        
        # Validar cadeia (deve estar OK)
        validation_before = validate_chain()
        
        # Simular tampering (modificar arquivo diretamente)
        with CHAIN_FILE.open("r") as f:
            lines = f.readlines()
        
        # Alterar um valor no primeiro bloco (phi: 0.8 -> 0.9)
        if lines:
            first_line = lines[0]
            tampered_line = first_line.replace('"phi":0.8', '"phi":0.9')
            lines[0] = tampered_line
        
        with CHAIN_FILE.open("w") as f:
            f.writelines(lines)
        
        # Validar cadeia (deve detectar tampering)
        validation_after = validate_chain()
        
        return {
            "test": "neural_chain_integrity",
            "validation_before": validation_before["valid"],
            "validation_after": validation_after["valid"],
            "tampering_detected": not validation_after["valid"],
            "error_count": len(validation_after["errors"]),
            "passed": validation_before["valid"] and not validation_after["valid"]
        }
    
    finally:
        # Restaurar backup se existir
        backup_file = CHAIN_FILE.with_suffix(".backup")
        if backup_file.exists():
            if CHAIN_FILE.exists():
                CHAIN_FILE.unlink()
            backup_file.rename(CHAIN_FILE)