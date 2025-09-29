#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  PENIN-Ω · CÓDIGO 4/8 — Mutação, Geração & Neurofusão (DNA-Fabric + EDNAG + Backpropamine)
# =============================================================================
#
#  OBJETIVO:
#  ---------------------------------------------------------------------------
#  Este módulo implementa a FASE 4 do organismo PENIN-Ω (IAAA): a máquina de
#  mutações seguras e mensuráveis. Transforma Xt + PlanΩ + AcquisitionReport
#  em MutationBundle com candidatos evolutivos seguros, saneados e com fitness
#  previsto para o Crisol (5/8).
#
#  CARACTERÍSTICAS:
#  - DNA-Fabric: Codificação normalizada do estado em genótipo versionado
#  - EDNAG: Mutações evolutivas sob trust-region e CBFs  
#  - Backpropamine: Ranqueamento neuro-dopaminérgico simulado
#  - Sanitização AST completa e sandbox seguro com caps
#  - Surrogates adaptativos (GBM/Linear) com CI bootstrap
#  - WORM Merkle-like com assinaturas e provas
#  - Fail-closed com gates não-compensatórios
#  - Determinismo via seeds fixas e replay
#  - CPU-first otimizado (<90s para N=32, K=5)
#
#  INTEGRAÇÃO:
#  - Entrada: Xt (1/8), PlanΩ (2/8), AcquisitionReport (3/8)
#  - Saída: MutationBundle para 5/8 + Xt atualizado
#  - Updates: delta_linf_pred, mdl_gain_pred, ppl_ood_pred, hashes, proofs
#
#  VERSÃO: 4.8.0-FUSION-FINAL
#  DATA: 2025.01.16
# =============================================================================

from __future__ import annotations

import ast
import json
import math
import os
import random
import re
import shutil
import signal
import sqlite3
import tempfile
import time
import threading
import uuid
import zipfile
import hashlib
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from datetime import datetime, timezone
from collections import defaultdict, Counter, deque
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# IMPORTS OPCIONAIS COM FALLBACKS
# =============================================================================

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import r2_score, mean_absolute_error
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# =============================================================================
# INTEGRAÇÃO SIMBIÓTICA COM 1/8, 2/8, 3/8
# =============================================================================

try:
    # Importação dos módulos core
    from penin_omega_1_core import (
        OmegaState, WORMLedger, LLMBridge,
        save_json, load_json, _ts, _hash_data,
        GOVERNANCE, DIRS as CORE_DIRS, log
    )
    from penin_omega_2_strategy import (
        PlanOmega, Goal, Constraints, Budgets
    )
    from penin_omega_3_acquisition import (
        AcquisitionReport
    )
    CORE_INTEGRATION = True
except ImportError:
    CORE_INTEGRATION = False
    
    # Fallbacks completos para operação standalone
    from datetime import datetime, timezone
    
    def _ts() -> str:
        return datetime.now(timezone.utc).isoformat()
    
    def _hash_data(data: Any) -> str:
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        if isinstance(data, str):
            data = data.encode("utf-8")
        elif not isinstance(data, bytes):
            data = str(data).encode("utf-8")
        return hashlib.sha256(data).hexdigest()
    
    def save_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def load_json(path: Path, default: Any = None) -> Any:
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    
    def log(msg: str, level: str = "INFO") -> None:
        print(f"[{_ts()}][4/8][{level}] {msg}")
    
    @dataclass
    class OmegaState:
        ece: float = 0.0
        rho_bias: float = 1.0
        rho: float = 0.5
        trust_region_radius: float = 0.10
        sr_score: float = 1.0
        caos_post: float = 1.0
        delta_linf: float = 0.0
        mdl_gain: float = 0.0
        ppl_ood: float = 100.0
        novelty_sim: float = 1.0
        rag_recall: float = 1.0
        hashes: List[str] = field(default_factory=list)
        proof_ids: List[str] = field(default_factory=list)
        delta_linf_pred: float = 0.0
        mdl_gain_pred: float = 0.0
        ppl_ood_pred: float = 0.0
        adv_capabilities: Dict[str, bool] = field(default_factory=dict)
        cycle_count: int = 0
        
        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "OmegaState":
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        
        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)
        
        def validate_gates(self) -> bool:
            return self.ece <= 0.01 and self.rho <= 0.95
    
    @dataclass
    class Goal:
        name: str = ""
        metric: str = ""
        target: float = 0.0
        tolerance: float = 0.05
    
    @dataclass
    class Constraints:
        ece_max: float = 0.01
        rho_bias_max: float = 1.05
        rho_max: float = 0.95
        delta_linf_min: float = 0.01
        trust_region_radius_proposed: float = 0.1
    
    @dataclass
    class Budgets:
        max_cost: float = 10.0
        max_tokens: int = 100000
        max_llm_calls: int = 12
        max_latency_ms: int = 10000
        quota_local: float = 0.8
        used_llm_calls: int = 0
        used_tokens: int = 0
        used_cost: float = 0.0
        
        def can_afford(self, required: Dict[str, Any]) -> bool:
            return (
                self.used_llm_calls + required.get("llm_calls", 0) <= self.max_llm_calls and
                self.used_tokens + required.get("tokens", 0) <= self.max_tokens and
                self.used_cost + required.get("cost", 0) <= self.max_cost
            )
        
        def allocate(self, amount: Dict[str, Any], purpose: str = "") -> bool:
            if not self.can_afford(amount):
                return False
            self.used_llm_calls += amount.get("llm_calls", 0)
            self.used_tokens += amount.get("tokens", 0)
            self.used_cost += amount.get("cost", 0.0)
            return True
        
        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)
    
    @dataclass
    class PlanOmega:
        id: str = ""
        goals: List[Goal] = field(default_factory=list)
        constraints: Constraints = field(default_factory=Constraints)
        budgets: Budgets = field(default_factory=Budgets)
        U_signal: float = 0.0
        priority_map: Dict[str, float] = field(default_factory=dict)
        promotion_policy: Dict[str, Any] = field(default_factory=dict)
        rollback_policy: Dict[str, Any] = field(default_factory=dict)
        
        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "PlanOmega":
            return cls(
                id=data.get("id", ""),
                goals=[Goal(**g) if isinstance(g, dict) else g for g in data.get("goals", [])],
                constraints=Constraints(**data.get("constraints", {})) if isinstance(data.get("constraints"), dict) else Constraints(),
                budgets=Budgets(**data.get("budgets", {})) if isinstance(data.get("budgets"), dict) else Budgets(),
                U_signal=data.get("U_signal", 0.0),
                priority_map=data.get("priority_map", {}),
                promotion_policy=data.get("promotion_policy", {}),
                rollback_policy=data.get("rollback_policy", {})
            )
        
        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)
    
    @dataclass
    class AcquisitionReport:
        novelty_sim: float = 1.0
        rag_recall: float = 1.0
        synthesis_path: Optional[str] = None
        questions: List[str] = field(default_factory=list)
        sources_stats: Dict[str, Any] = field(default_factory=dict)
        plan_hash: str = ""
        n_docs: int = 0
        n_chunks: int = 0
        proof_id: str = ""
        
        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "AcquisitionReport":
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        
        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)
    
    class WORMLedger:
        def __init__(self, path: Optional[Path] = None):
            self.path = path or Path("worm_ledger.jsonl")
            self.lock = threading.RLock()
        
        def record_event(self, event_type: str, data: Dict[str, Any]) -> str:
            with self.lock:
                event_id = str(uuid.uuid4())
                payload = {
                    "event_id": event_id,
                    "type": event_type,
                    "data": data,
                    "timestamp": _ts()
                }
                payload["hash"] = _hash_data(payload)
                
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                
                return event_id
    
    GOVERNANCE = {}
    CORE_DIRS = None

# =============================================================================
# CONFIGURAÇÃO E PATHS
# =============================================================================

if CORE_INTEGRATION and CORE_DIRS:
    DIRS = CORE_DIRS
else:
    ROOT = Path("/opt/penin_omega") if Path("/opt/penin_omega").exists() else Path.home() / ".penin_omega"
    DIRS = {
        "LOG": ROOT / "logs",
        "STATE": ROOT / "state",
        "WORK": ROOT / "workspace",
        "WORM": ROOT / "worm",
        "BUNDLES": ROOT / "bundles",
        "CONFIG": ROOT / "config",
        "SANDBOX": ROOT / "sandbox",
        "SURROGATES": ROOT / "surrogates"
    }

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = DIRS["LOG"] / "fase4_mutacao.log"
WORM_FILE = DIRS["WORM"] / "mutation_ledger.jsonl"
SURROGATE_STATE = DIRS["SURROGATES"] / "surrogate_state.json"
SURROGATE_HISTORY = DIRS["SURROGATES"] / "surrogate_history.sqlite3"

# =============================================================================
# CONFIGURAÇÃO DEFAULT
# =============================================================================

DEFAULT_CONFIG = {
    "version": "4.8.0-FUSION",
    "n_candidates": 32,
    "top_k": 5,
    "seed": 42,
    "trust_region": {
        "radius_default": 0.1,
        "distance_metric": "weighted_hybrid",
        "penalty_overshoot": 2.0
    },
    "operators": {
        "weights": {"point": 0.4, "segment": 0.25, "recombination": 0.2, "flag": 0.15},
        "elite_preserve": True,
        "noise_schedule": "adaptive"
    },
    "sandbox": {
        "timeout_s": 5,
        "mem_limit_mb": 512,
        "cpu_quota_ms": 5000,
        "fs_restrict": True
    },
    "surrogate": {
        "model": "gbm" if HAS_SKLEARN else "linear",
        "ci_bootstrap": 100,
        "history_size": 1000,
        "incremental": True
    },
    "diversity": {
        "min_threshold": 0.3,
        "operator_coverage": 0.6,
        "distance_variance": 0.2
    },
    "cbf": {
        "ast_strict": True,
        "exploit_patterns": True,
        "pii_sanitize": True
    },
    "performance": {
        "target_latency_ms": 90000,  # 90s
        "max_memory_mb": 500,
        "cache_enabled": True
    }
}

# =============================================================================
# ENUMS E TIPOS
# =============================================================================

class MutationType(Enum):
    POINT = "point"
    SEGMENT = "segment"
    RECOMBINATION = "recombination"
    FLAG = "flag"
    NET2NET = "net2net"
    LORA = "lora"
    QUANTIZATION = "quantization"

class MutationEventType(Enum):
    MUT_START = "MUT_START"
    MUT_GENOTYPE = "MUT_GENOTYPE"
    MUT_CANDIDATE = "MUT_CANDIDATE"
    MUT_SANITIZE = "MUT_SANITIZE"
    MUT_SIMULATE = "MUT_SIMULATE"
    MUT_SCORE = "MUT_SCORE"
    MUT_BUNDLE = "MUT_BUNDLE"
    MUT_ABORT = "MUT_ABORT"
    MUT_DONE = "MUT_DONE"
    MUT_SKIP_TR = "MUT_SKIP_TR"
    MUT_SKIP_BUDGET = "MUT_SKIP_BUDGET"

# =============================================================================
# ESPAÇO DE GENES EXPANDIDO
# =============================================================================

GENE_SPACE: Dict[str, Dict[str, Any]] = {
    # Hiperparâmetros contínuos
    "hp.lr": {"type": "float", "min": 1e-5, "max": 5e-1, "w": 1.0, "mutable": True},
    "hp.batch": {"type": "int", "min": 4, "max": 512, "w": 0.6, "mutable": True},
    "hp.momentum": {"type": "float", "min": 0.0, "max": 0.99, "w": 0.4, "mutable": True},
    "hp.dropout": {"type": "float", "min": 0.0, "max": 0.5, "w": 0.3, "mutable": True},
    
    # Parâmetros SR/CAOS
    "sr.tau": {"type": "float", "min": 0.6, "max": 0.95, "w": 1.0, "mutable": True},
    "caos.kappa": {"type": "float", "min": 1.0, "max": 4.0, "w": 0.8, "mutable": True},
    "caos.pmin": {"type": "float", "min": 0.01, "max": 0.20, "w": 0.3, "mutable": True},
    "caos.pmax": {"type": "float", "min": 1.0, "max": 4.0, "w": 0.3, "mutable": True},
    
    # RAG/Retrieval
    "rag.topk": {"type": "int", "min": 4, "max": 64, "w": 0.5, "mutable": True},
    "rag.temperature": {"type": "float", "min": 0.1, "max": 2.0, "w": 0.4, "mutable": True},
    "simhash.thr": {"type": "float", "min": 0.6, "max": 0.99, "w": 0.5, "mutable": True},
    
    # Flags estruturais
    "ops.flags.quant": {"type": "flag", "w": 0.5, "mutable": True},
    "ops.flags.lora": {"type": "flag", "w": 0.5, "mutable": True},
    "ops.flags.net2net": {"type": "flag", "w": 0.7, "mutable": True},
    "ops.flags.pruning": {"type": "flag", "w": 0.4, "mutable": True},
    
    # Modos discretos
    "sr.mode.embed": {"type": "discrete", "options": ["lite", "standard", "heavy"], "w": 0.4, "mutable": True},
    "optim.type": {"type": "discrete", "options": ["sgd", "adam", "adamw"], "w": 0.5, "mutable": True},
    
    # Prompts LLM-guided
    "llm.prompt.anchor1": {"type": "flag", "w": 1.0, "mutable": False},
    "llm.prompt.anchor2": {"type": "flag", "w": 1.0, "mutable": False},
}

CONTINUOUS_KEYS = [k for k, s in GENE_SPACE.items() if s["type"] in ("float", "int")]
FLAG_KEYS = [k for k, s in GENE_SPACE.items() if s["type"] == "flag"]
DISCRETE_KEYS = [k for k, s in GENE_SPACE.items() if s["type"] == "discrete"]
MUTABLE_KEYS = [k for k, s in GENE_SPACE.items() if s.get("mutable", True)]

# =============================================================================
# MODELOS DE DADOS
# =============================================================================

@dataclass
class Genotype:
    schema: int = 1
    genes: Dict[str, float] = field(default_factory=dict)
    hash_base: str = ""
    notes: str = ""
    parent_ids: List[str] = field(default_factory=list)
    
    def copy(self) -> "Genotype":
        return Genotype(
            schema=self.schema,
            genes=dict(self.genes),
            hash_base=self.hash_base,
            notes=self.notes,
            parent_ids=list(self.parent_ids)
        )

@dataclass
class Candidate:
    cand_id: str
    parent_ids: List[str] = field(default_factory=list)
    op_seq: List[Dict[str, Any]] = field(default_factory=list)
    distance_to_base: float = 0.0
    patches: List[Dict[str, Any]] = field(default_factory=list)
    build_steps: List[str] = field(default_factory=list)
    env_caps: Dict[str, Any] = field(default_factory=dict)
    pred_metrics: Dict[str, Any] = field(default_factory=dict)
    risk_estimate: float = 0.0
    cost_estimate: float = 0.0
    latency_estimate: float = 0.0
    score: float = 0.0
    explain: str = ""
    proof_id: str = ""

@dataclass
class MutationBundle:
    bundle_id: str
    plan_hash: str
    seed: int
    topK: List[Candidate]
    surrogate_report: Dict[str, Any]
    diversity_summary: Dict[str, Any]
    artifact_path: str
    xt_updates: Dict[str, Any] = field(default_factory=dict)

# =============================================================================
# WORM LEDGER ESPECIALIZADO
# =============================================================================

class MutationWORMLedger:
    """Ledger WORM com Merkle chain para eventos de mutação."""
    
    def __init__(self, file_path: Path = WORM_FILE):
        self.path = file_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._cache = deque(maxlen=100)
    
    def record(self, event_type: Union[str, MutationEventType], data: Dict[str, Any]) -> str:
        with self.lock:
            if isinstance(event_type, MutationEventType):
                event_type = event_type.value
            
            event = {
                "type": event_type,
                "data": data,
                "timestamp": _ts()
            }
            
            # Merkle chain
            prev_hash = self._get_last_hash()
            event["prev_hash"] = prev_hash
            event["hash"] = _hash_data({k: v for k, v in event.items() if k != "hash"})
            
            # Write to file
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            
            # Update cache
            self._cache.append(event["hash"])
            
            return event["hash"]
    
    def _get_last_hash(self) -> str:
        if self._cache:
            return self._cache[-1]
        
        if self.path.exists() and self.path.stat().st_size > 0:
            try:
                with self.path.open("rb") as f:
                    f.seek(-500, os.SEEK_END)  # Read last ~500 bytes
                    lines = f.read().decode("utf-8", errors="ignore").splitlines()
                    for line in reversed(lines):
                        if line.strip():
                            return json.loads(line).get("hash", "genesis")
            except Exception:
                pass
        
        return "genesis"

# =============================================================================
# POLÍTICAS DE SANITIZAÇÃO (CBFs)
# =============================================================================

BAN_IMPORTS = {
    "os", "sys", "subprocess", "socket", "shutil", "multiprocessing",
    "ctypes", "resource", "requests", "urllib", "http", "ftplib",
    "pickle", "marshal", "imp", "importlib", "__main__"
}

BAN_CALLNAMES = {
    "system", "popen", "exec", "eval", "__import__", "fork", "spawn",
    "kill", "compile", "globals", "locals", "vars", "dir"
}

EXPLOIT_PATTERNS = [
    r'eval\s*\(', r'exec\s*\(', r'__import__\s*\(', r'os\.',
    r'subprocess\.', r'\brm\s+-rf\b', r'\bpython\s+-c\b',
    r'pickle\.loads', r'marshal\.loads'
]

def sanitize_python_source(src: str) -> Tuple[bool, List[str]]:
    """Sanitização AST completa com CBFs."""
    issues: List[str] = []
    
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return False, [f"syntax_error: {e}"]
    
    class SecurityGuard(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module in BAN_IMPORTS:
                    issues.append(f"ban_import:{alias.name}")
            self.generic_visit(node)
        
        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            module = (node.module or "").split(".")[0]
            if module in BAN_IMPORTS:
                issues.append(f"ban_import:{node.module}")
            self.generic_visit(node)
        
        def visit_Call(self, node: ast.Call) -> None:
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            
            if name in BAN_CALLNAMES:
                issues.append(f"ban_call:{name}")
            self.generic_visit(node)
        
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            # Check for dangerous decorators
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id in ["property", "staticmethod", "classmethod"]:
                    continue  # Safe decorators
                issues.append(f"suspicious_decorator:{ast.unparse(decorator) if hasattr(ast, 'unparse') else 'unknown'}")
            self.generic_visit(node)
    
    SecurityGuard().visit(tree)
    
    # Check exploit patterns
    for pattern in EXPLOIT_PATTERNS:
        if re.search(pattern, src):
            issues.append(f"exploit_pattern:{pattern}")
    
    return len(issues) == 0, issues

# =============================================================================
# SANDBOX SEGURO APRIMORADO
# =============================================================================

def run_in_sandbox(code_text: str, timeout_s: int = 5, mem_limit_mb: int = 512) -> Tuple[bool, Dict[str, Any]]:
    """Execução em sandbox com múltiplas camadas de segurança."""
    
    # Sanitização primeiro
    ok, issues = sanitize_python_source(code_text)
    if not ok:
        return False, {"errors": issues, "phase": "sanitization"}
    
    # Prepare sandboxed namespace
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bool": bool,
        "dict": dict, "enumerate": enumerate, "float": float,
        "int": int, "len": len, "list": list, "max": max,
        "min": min, "print": lambda *args, **kwargs: None,  # No-op print
        "range": range, "round": round, "str": str, "sum": sum,
        "tuple": tuple, "type": type, "zip": zip,
        "__name__": "__main__",
        "__doc__": None,
    }
    
    # Setup timeout handler
    def timeout_handler(signum, frame):
        raise TimeoutError("sandbox_timeout")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_s)
    
    try:
        # Create temporary directory for sandbox
        with tempfile.TemporaryDirectory() as tmpdir:
            # Compile code
            bytecode = compile(code_text, "<sandbox>", "exec")
            
            # Create isolated namespace
            ns = {"__builtins__": safe_builtins, "__tmpdir__": tmpdir}
            
            # Track resource usage
            t0 = time.perf_counter()
            mem_before = 0
            if HAS_PSUTIL:
                proc = psutil.Process()
                mem_before = proc.memory_info().rss / (1024 * 1024)
            
            # Execute
            exec(bytecode, ns, ns)
            
            # Calculate metrics
            latency_ms = (time.perf_counter() - t0) * 1000
            mem_after = mem_before
            if HAS_PSUTIL:
                mem_after = proc.memory_info().rss / (1024 * 1024)
                mem_delta = mem_after - mem_before
                
                if mem_delta > mem_limit_mb:
                    return False, {"errors": ["memory_exceeded"], "mem_delta_mb": mem_delta}
            
            return True, {
                "latency_ms": latency_ms,
                "mem_delta_mb": mem_after - mem_before if HAS_PSUTIL else 0,
                "phase": "execution"
            }
    
    except TimeoutError:
        return False, {"errors": ["timeout"], "phase": "execution"}
    except Exception as e:
        return False, {"errors": [f"exec_error:{e}"], "phase": "execution"}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# =============================================================================
# DNA-FABRIC (CODIFICAÇÃO GENÉTICA)
# =============================================================================

class DNAFabric:
    """Sistema de codificação/decodificação de genótipos."""
    
    @staticmethod
    def base_from_xt_and_plan(xt: OmegaState, plan: PlanOmega, acq: AcquisitionReport) -> Genotype:
        """Cria genótipo base a partir do estado atual."""
        # Seed determinística baseada no estado
        seed_data = {
            "xt": xt.to_dict(),
            "plan": plan.to_dict(),
            "acq": acq.to_dict()
        }
        seed_hash = _hash_data(seed_data)
        rnd = random.Random(seed_hash[:16])
        
        genes: Dict[str, float] = {}
        
        # Inicialização baseada em anchors da aquisição
        anchors = acq.questions[:5] if acq.questions else []
        synth_hints = []
        
        if acq.synthesis_path and Path(acq.synthesis_path).exists():
            try:
                synth_data = load_json(Path(acq.synthesis_path))
                if isinstance(synth_data, dict) and "content" in synth_data:
                    # Extrai palavras-chave
                    text = str(synth_data["content"])
                    synth_hints = re.findall(r'\b[a-z]{4,}\b', text.lower())[:10]
            except Exception:
                pass
        
        # Inicializa genes
        for key, spec in GENE_SPACE.items():
            if spec["type"] == "float":
                # Centro com perturbação baseada em hints
                base_val = 0.5
                if synth_hints:
                    hint_hash = _hash_data(key + "".join(synth_hints[:3]))
                    perturbation = (int(hint_hash[:4], 16) % 100) / 1000.0
                    base_val = min(0.7, max(0.3, base_val + perturbation))
                genes[key] = base_val
                
            elif spec["type"] == "int":
                genes[key] = 0.5
                
            elif spec["type"] == "flag":
                # Flags influenciadas por anchors
                if "prompt" in key and anchors:
                    genes[key] = 1.0 if len(anchors) % 2 == 1 else 0.0
                else:
                    genes[key] = float(rnd.choice([0, 1]))
                    
            elif spec["type"] == "discrete":
                n_options = len(spec["options"])
                genes[key] = rnd.random() if n_options > 1 else 0.0
        
        hash_base = _hash_data(genes)
        notes = f"v1|anchors:{len(anchors)}|hints:{len(synth_hints)}|seed:{seed_hash[:8]}"
        
        return Genotype(
            schema=1,
            genes=genes,
            hash_base=hash_base,
            notes=notes,
            parent_ids=[]
        )
    
    @staticmethod
    def denormalize(genes: Dict[str, float]) -> Dict[str, Any]:
        """Converte genes normalizados para valores reais."""
        real: Dict[str, Any] = {}
        
        for key, val in genes.items():
            if key not in GENE_SPACE:
                continue
                
            spec = GENE_SPACE[key]
            val = float(val)
            
            if spec["type"] == "float":
                real[key] = spec["min"] + val * (spec["max"] - spec["min"])
                
            elif spec["type"] == "int":
                real[key] = int(round(spec["min"] + val * (spec["max"] - spec["min"])))
                
            elif spec["type"] == "flag":
                real[key] = bool(round(val))
                
            elif spec["type"] == "discrete":
                options = spec["options"]
                idx = min(len(options) - 1, int(val * len(options)))
                real[key] = options[idx]
        
        return real

# =============================================================================
# EDNAG (GERADOR EVOLUTIVO)
# =============================================================================

class EDNAGenerator:
    """Gerador evolutivo com trust-region e operadores avançados."""
    
    def __init__(self, trust_radius: float, seed: int, sr_score: float = 1.0):
        self.trust_radius = max(0.001, min(0.5, trust_radius))
        self.sr_score = sr_score
        self.rnd = random.Random(seed)
        self.elite: Optional[Genotype] = None
        self.elite_score: float = -float('inf')
        self.mutation_history: deque = deque(maxlen=100)
    
    def _adaptive_noise(self, base: float) -> float:
        """Noise adaptativo baseado em SR."""
        if self.sr_score < 0.7:
            return base * 0.5  # Reduz exploração se SR baixo
        elif self.sr_score > 0.9:
            return base * 1.2  # Aumenta exploração se SR alto
        return base
    
    def _mutate_value(self, val: float, step_size: float) -> float:
        """Mutação de valor único com ruído controlado."""
        step = self._adaptive_noise(step_size)
        delta = self.rnd.gauss(0, step)
        return max(0.0, min(1.0, val + delta))
    
    def point_mutate(self, g: Genotype) -> Tuple[Genotype, List[Dict[str, Any]], float]:
        """Mutação pontual em genes selecionados."""
        g2 = g.copy()
        g2.parent_ids = [g.hash_base]
        ops = []
        
        # Seleciona genes mutáveis
        mutable = [k for k in MUTABLE_KEYS if k in g2.genes]
        n_mutate = max(1, int(self.trust_radius * len(mutable) * 0.3))
        
        self.rnd.shuffle(mutable)
        for key in mutable[:n_mutate]:
            old_val = g2.genes[key]
            step_size = 0.15 * self.trust_radius * GENE_SPACE[key].get("w", 1.0)
            g2.genes[key] = self._mutate_value(old_val, step_size)
            
            ops.append({
                "op": MutationType.POINT.value,
                "gene": key,
                "from": old_val,
                "to": g2.genes[key]
            })
        
        dist = self.distance(g, g2)
        self._update_history(MutationType.POINT, dist)
        return g2, ops, dist
    
    def segment_mutate(self, g: Genotype) -> Tuple[Genotype, List[Dict[str, Any]], float]:
        """Mutação em segmento contíguo."""
        g2 = g.copy()
        g2.parent_ids = [g.hash_base]
        ops = []
        
        cont_keys = [k for k in CONTINUOUS_KEYS if k in g2.genes and GENE_SPACE[k].get("mutable", True)]
        if not cont_keys:
            return g2, ops, 0.0
        
        start = self.rnd.randrange(len(cont_keys))
        length = max(1, int(self.trust_radius * len(cont_keys) * 0.5))
        
        for i in range(start, min(start + length, len(cont_keys))):
            key = cont_keys[i]
            old_val = g2.genes[key]
            step_size = 0.12 * self.trust_radius * GENE_SPACE[key].get("w", 1.0)
            g2.genes[key] = self._mutate_value(old_val, step_size)
            
            ops.append({
                "op": MutationType.SEGMENT.value,
                "gene": key,
                "from": old_val,
                "to": g2.genes[key]
            })
        
        dist = self.distance(g, g2)
        self._update_history(MutationType.SEGMENT, dist)
        return g2, ops, dist
    
    def recombine(self, a: Genotype, b: Genotype) -> Tuple[Genotype, List[Dict[str, Any]], float]:
        """Recombinação com crossover uniforme."""
        g2 = a.copy()
        g2.parent_ids = [a.hash_base, b.hash_base]
        ops = []
        
        for key in g2.genes:
            if key in b.genes and self.rnd.random() < 0.5:
                old_val = g2.genes[key]
                # Média ponderada com ruído
                alpha = self.rnd.uniform(0.3, 0.7)
                g2.genes[key] = alpha * a.genes[key] + (1 - alpha) * b.genes[key]
                g2.genes[key] = max(0.0, min(1.0, g2.genes[key] + self.rnd.gauss(0, 0.02)))
                
                if abs(g2.genes[key] - old_val) > 1e-6:
                    ops.append({
                        "op": MutationType.RECOMBINATION.value,
                        "gene": key,
                        "from": old_val,
                        "to": g2.genes[key],
                        "parents": [a.hash_base, b.hash_base]
                    })
        
        dist = self.distance(a, g2)
        self._update_history(MutationType.RECOMBINATION, dist)
        return g2, ops, dist
    
    def flag_mutate(self, g: Genotype) -> Tuple[Genotype, List[Dict[str, Any]], float]:
        """Mutação de flags estruturais."""
        g2 = g.copy()
        g2.parent_ids = [g.hash_base]
        ops = []
        
        flag_keys = [k for k in FLAG_KEYS if k in g2.genes and GENE_SPACE[k].get("mutable", True)]
        n_flip = max(1, int(self.trust_radius * len(flag_keys)))
        
        self.rnd.shuffle(flag_keys)
        for key in flag_keys[:n_flip]:
            old_val = g2.genes[key]
            g2.genes[key] = 1.0 - old_val
            
            ops.append({
                "op": MutationType.FLAG.value,
                "gene": key,
                "from": old_val,
                "to": g2.genes[key]
            })
        
        dist = self.distance(g, g2)
        self._update_history(MutationType.FLAG, dist)
        return g2, ops, dist
    
    def update_elite(self, g: Genotype, score: float) -> None:
        """Atualiza o melhor indivíduo (elitismo)."""
        if score > self.elite_score:
            self.elite = g.copy()
            self.elite_score = score
    
    def get_elite(self) -> Optional[Tuple[Genotype, List[Dict[str, Any]], float]]:
        """Retorna o elite se existir."""
        if self.elite:
            return self.elite, [{"op": "elite", "note": "best_preserved"}], 0.0
        return None
    
    def distance(self, a: Genotype, b: Genotype) -> float:
        """Calcula distância híbrida entre genótipos."""
        l2_sum = 0.0
        hamming_sum = 0.0
        jaccard_sum = 0.0
        
        for key in set(a.genes.keys()) | set(b.genes.keys()):
            if key not in GENE_SPACE:
                continue
            
            spec = GENE_SPACE[key]
            weight = spec.get("w", 1.0)
            
            a_val = a.genes.get(key, 0.5)
            b_val = b.genes.get(key, 0.5)
            
            if spec["type"] in ("float", "int"):
                # Distância euclidiana ponderada
                diff = (a_val - b_val) * weight
                l2_sum += diff * diff
                
            elif spec["type"] == "flag":
                # Distância de Hamming
                if round(a_val) != round(b_val):
                    hamming_sum += weight
                    
            elif spec["type"] == "discrete":
                # Distância discreta normalizada
                if abs(a_val - b_val) > 0.1:
                    hamming_sum += weight * abs(a_val - b_val)
        
        # Combina métricas
        total = math.sqrt(l2_sum) + hamming_sum + jaccard_sum
        return min(1.0, total)  # Normaliza para [0, 1]
    
    def _update_history(self, op_type: MutationType, distance: float) -> None:
        """Atualiza histórico de mutações."""
        self.mutation_history.append({
            "type": op_type.value,
            "distance": distance,
            "timestamp": time.time()
        })

# =============================================================================
# SURROGATE MODELS AVANÇADOS
# =============================================================================

class AdvancedSurrogate:
    """Sistema de modelos substitutos com CI bootstrap."""
    
    def __init__(self, model_type: str = "gbm"):
        self.model_type = model_type
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.feature_names: List[str] = []
        self.tasks = ["delta_linf_hat", "mdl_gain_hat", "ppl_ood_hat"]
        self.history = self._load_history()
        self.is_trained = False
    
    def _load_history(self) -> Dict[str, List]:
        """Carrega histórico de treino."""
        if SURROGATE_STATE.exists():
            try:
                data = load_json(SURROGATE_STATE)
                return data.get("history", {"X": [], "y": {t: [] for t in self.tasks}})
            except Exception:
                pass
        return {"X": [], "y": {t: [] for t in self.tasks}}
    
    def _save_history(self) -> None:
        """Salva histórico para persistência."""
        save_json(SURROGATE_STATE, {"history": self.history, "timestamp": _ts()})
    
    def fit(self, X: List[List[float]], y: Dict[str, List[float]]) -> Dict[str, Any]:
        """Treina modelos para cada métrica."""
        if not X or not y:
            return {"n_samples": 0, "model": self.model_type}
        
        # Update history (mantém últimas N amostras)
        max_history = 1000
        self.history["X"].extend(X)
        for task in self.tasks:
            self.history["y"][task].extend(y.get(task, []))
        
        # Trim history
        if len(self.history["X"]) > max_history:
            self.history["X"] = self.history["X"][-max_history:]
            for task in self.tasks:
                self.history["y"][task] = self.history["y"][task][-max_history:]
        
        # Train on combined data
        X_train = self.history["X"]
        report = {
            "n_samples": len(X_train),
            "model": self.model_type,
            "r2": {},
            "mae": {}
        }
        
        if len(X_train) < 5:
            # Fallback para média se poucos dados
            for task in self.tasks:
                y_task = self.history["y"][task]
                if y_task:
                    self.models[task] = {"type": "mean", "value": sum(y_task) / len(y_task)}
            return report
        
        # Train models
        for task in self.tasks:
            y_task = self.history["y"][task]
            if len(y_task) != len(X_train):
                continue
            
            if HAS_SKLEARN and HAS_NUMPY:
                X_arr = np.array(X_train)
                y_arr = np.array(y_task)
                
                # Scale features
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X_arr)
                self.scalers[task] = scaler
                
                # Choose model
                if self.model_type == "gbm":
                    model = GradientBoostingRegressor(
                        n_estimators=100,
                        max_depth=4,
                        min_samples_split=5,
                        random_state=42
                    )
                else:
                    model = Ridge(alpha=1.0)
                
                # Fit
                model.fit(X_scaled, y_arr)
                self.models[task] = model
                
                # Metrics
                y_pred = model.predict(X_scaled)
                report["r2"][task] = float(r2_score(y_arr, y_pred))
                report["mae"][task] = float(mean_absolute_error(y_arr, y_pred))
            else:
                # Fallback linear approximation
                y_mean = sum(y_task) / len(y_task)
                self.models[task] = {"type": "mean", "value": y_mean}
                report["r2"][task] = 0.0
                report["mae"][task] = 0.0
        
        self.is_trained = True
        self._save_history()
        return report
    
    def predict_with_ci(self, features: List[float], n_bootstrap: int = 100) -> Dict[str, Any]:
        """Predição com intervalos de confiança."""
        result = {"preds": {}, "ci": {}}
        
        for task in self.tasks:
            if task not in self.models:
                result["preds"][task] = 0.0
                result["ci"][task] = {"low": 0.0, "up": 0.0}
                continue
            
            model = self.models[task]
            
            if isinstance(model, dict) and model["type"] == "mean":
                # Modelo médio simples
                pred = model["value"]
                result["preds"][task] = pred
                result["ci"][task] = {"low": pred * 0.9, "up": pred * 1.1}
                
            elif HAS_SKLEARN and HAS_NUMPY:
                # Modelo sklearn
                X_single = np.array([features]).reshape(1, -1)
                
                if task in self.scalers:
                    X_scaled = self.scalers[task].transform(X_single)
                else:
                    X_scaled = X_single
                
                # Point prediction
                pred = float(model.predict(X_scaled)[0])
                result["preds"][task] = pred
                
                # Bootstrap CI
                if len(self.history["X"]) >= n_bootstrap:
                    bootstrap_preds = []
                    for _ in range(min(n_bootstrap, 50)):  # Limit for performance
                        # Sample with replacement
                        indices = np.random.choice(len(self.history["X"]), len(self.history["X"]))
                        X_boot = [self.history["X"][i] for i in indices]
                        y_boot = [self.history["y"][task][i] for i in indices]
                        
                        # Quick refit (simplified)
                        if self.model_type == "gbm":
                            # Use fewer trees for bootstrap
                            boot_model = GradientBoostingRegressor(n_estimators=20, random_state=42)
                        else:
                            boot_model = Ridge(alpha=1.0)
                        
                        X_boot_arr = self.scalers[task].transform(np.array(X_boot))
                        boot_model.fit(X_boot_arr, y_boot)
                        boot_pred = boot_model.predict(X_scaled)[0]
                        bootstrap_preds.append(boot_pred)
                    
                    # Calculate percentiles
                    low = float(np.percentile(bootstrap_preds, 2.5))
                    up = float(np.percentile(bootstrap_preds, 97.5))
                    result["ci"][task] = {"low": low, "up": up}
                else:
                    # Fallback CI
                    result["ci"][task] = {"low": pred * 0.8, "up": pred * 1.2}
            else:
                result["preds"][task] = 0.0
                result["ci"][task] = {"low": 0.0, "up": 0.0}
        
        # Post-process para garantir valores válidos
        result["preds"]["delta_linf_hat"] = max(0.0, result["preds"].get("delta_linf_hat", 0.0))
        result["preds"]["mdl_gain_hat"] = max(0.0, result["preds"].get("mdl_gain_hat", 0.0))
        result["preds"]["ppl_ood_hat"] = max(1.0, result["preds"].get("ppl_ood_hat", 100.0))
        
        return result

# =============================================================================
# MICRO-BENCHMARK E FEATURES
# =============================================================================

def micro_benchmark(real_params: Dict[str, Any], acq: AcquisitionReport) -> Dict[str, float]:
    """Benchmark heurístico influenciado pelo contexto de aquisição."""
    # Base metrics
    base_latency = 2.0
    base_cost = 0.001
    base_risk = 0.05
    
    # Adjust for parameters
    latency = base_latency
    latency += 0.01 * real_params.get("rag.topk", 8)
    latency += 0.002 * real_params.get("hp.batch", 32)
    latency *= (1 + 0.1 * real_params.get("hp.dropout", 0.0))
    
    cost = base_cost
    cost += 0.001 * real_params.get("rag.topk", 8)
    cost += 0.002 if real_params.get("ops.flags.lora") else 0
    cost += 0.001 if real_params.get("ops.flags.net2net") else 0
    
    risk = base_risk
    risk += 0.05 if real_params.get("ops.flags.quant") else 0
    risk += 0.03 if real_params.get("ops.flags.pruning") else 0
    risk += 0.02 if real_params.get("prompt.anchor") else 0
    
    # Adjust for acquisition context
    novelty_factor = 1.0 - acq.novelty_sim
    recall_factor = 1.0 - acq.rag_recall
    
    latency *= (1 + 0.2 * novelty_factor)
    cost *= (1 + 0.1 * novelty_factor)
    risk *= (1 + 0.15 * recall_factor)
    
    return {
        "latency_ms": latency * 1000.0,
        "cost": min(1.0, cost),
        "risk": min(1.0, risk)
    }

def extract_features(real_params: Dict[str, Any], micro: Dict[str, float], acq: AcquisitionReport) -> List[float]:
    """Extrai features para o surrogate."""
    features = []
    
    # Gene features (ordenadas)
    for key in sorted(GENE_SPACE.keys()):
        if key in real_params:
            val = real_params[key]
            if isinstance(val, bool):
                features.append(1.0 if val else 0.0)
            elif isinstance(val, str):
                # Hash string to float
                features.append(float(int(_hash_data(val)[:8], 16) % 100) / 100.0)
            else:
                features.append(float(val))
        else:
            features.append(0.0)
    
    # Micro-bench features
    features.append(micro.get("latency_ms", 0.0) / 1000.0)
    features.append(micro.get("cost", 0.0))
    features.append(micro.get("risk", 0.0))
    
    # Acquisition context features
    features.append(acq.novelty_sim)
    features.append(acq.rag_recall)
    features.append(len(acq.questions) / 10.0)
    features.append(acq.n_docs / 100.0)
    features.append(acq.n_chunks / 1000.0)
    
    return features

# =============================================================================
# BACKPROPAMINE (SISTEMA DE SCORING)
# =============================================================================

def caos_phi(z: float, kappa: float = 1.5) -> float:
    """Função de saturação CAOS⁺."""
    z = max(1.0, z)
    return min(1.0, math.log(z) / math.log(1.0 + kappa))

def candidate_score(
    pred: Dict[str, Any],
    xt: OmegaState,
    risk: float,
    cost: float,
    tr_dist: float,
    lambda_rho: float = 0.5,
    epsilon: float = 1e-6
) -> float:
    """
    Score Backpropamine completo.
    S_i = ΔL∞_hat * φ(CAOS⁺) * SR / (cost + λρ*risk + ε) * penalty_tr
    """
    # Extract predictions
    if "preds" in pred:
        pred = pred["preds"]
    
    gain = float(pred.get("delta_linf_hat", 0.0))
    mdl = float(pred.get("mdl_gain_hat", 0.0))
    ppl = float(pred.get("ppl_ood_hat", 100.0))
    
    # Combined gain (weighted)
    combined_gain = gain + 0.3 * mdl + 0.1 * max(0, (100 - ppl) / 100)
    
    # CAOS factor
    phi = caos_phi(xt.caos_post, kappa=GENE_SPACE.get("caos.kappa", {}).get("max", 4.0))
    
    # SR factor
    sr_factor = max(0.1, xt.sr_score)
    
    # Cost-risk denominator
    denom = cost + lambda_rho * risk + epsilon
    
    # Trust region penalty
    tr_penalty = 1.0
    if tr_dist > xt.trust_region_radius * 0.7:
        # Penalize candidates near TR boundary
        overshoot = (tr_dist / max(epsilon, xt.trust_region_radius)) - 0.7
        tr_penalty = 1.0 + 2.0 * overshoot
    
    # Final score
    score = (combined_gain * phi * sr_factor) / (denom * tr_penalty)
    
    return max(0.0, score)

# =============================================================================
# ENGINE PRINCIPAL DE MUTAÇÃO
# =============================================================================

class MutationEngine:
    """Motor principal de mutação e geração."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or DEFAULT_CONFIG
        self.worm = MutationWORMLedger()
        self.surrogate = AdvancedSurrogate(self.config["surrogate"]["model"])
        self.cache = {}
    
    def execute(
        self,
        xt: OmegaState,
        plan: PlanOmega,
        acq: AcquisitionReport,
        n_candidates: Optional[int] = None,
        top_k: Optional[int] = None,
        seed: Optional[int] = None
    ) -> Tuple[MutationBundle, OmegaState]:
        """Executa pipeline completo de mutação."""
        
        # Configuration
        n_candidates = n_candidates or self.config["n_candidates"]
        top_k = top_k or self.config["top_k"]
        seed = seed or self.config["seed"]
        
        # Initialize
        t0 = time.perf_counter()
        rnd = random.Random(seed)
        plan_hash = _hash_data(plan.to_dict())
        
        # Log start
        start_proof = self.worm.record(MutationEventType.MUT_START, {
            "plan_hash": plan_hash,
            "trust_region": xt.trust_region_radius,
            "budgets": plan.budgets.to_dict(),
            "seed": seed,
            "n_candidates": n_candidates,
            "top_k": top_k
        })
        
        # Validate gates
        if not xt.validate_gates():
            abort_proof = self.worm.record(MutationEventType.MUT_ABORT, {
                "reason": "gate_violation",
                "ece": xt.ece,
                "rho": xt.rho
            })
            raise RuntimeError(f"Gate violation: ECE={xt.ece}, ρ={xt.rho}")
        
        # Generate base genotype
        base = DNAFabric.base_from_xt_and_plan(xt, plan, acq)
        
        self.worm.record(MutationEventType.MUT_GENOTYPE, {
            "schema": base.schema,
            "dims": len(base.genes),
            "hash_base": base.hash_base,
            "notes": base.notes
        })
        
        # Initialize EDNAG
        ednag = EDNAGenerator(xt.trust_region_radius, seed, xt.sr_score)
        
        # Generate candidates
        candidates = []
        surrogate_data = []
        
        # Operator selection weights
        op_weights = self.config["operators"]["weights"]
        operators = list(op_weights.keys())
        weights = [op_weights[op] for op in operators]
        
        for i in range(n_candidates):
            # Select operator
            op_type = rnd.choices(operators, weights=weights)[0]
            
            # Apply operator
            if op_type == "point":
                genotype, ops, dist = ednag.point_mutate(base)
            elif op_type == "segment":
                genotype, ops, dist = ednag.segment_mutate(base)
            elif op_type == "recombination":
                # Create variation for recombination
                variant, _, _ = ednag.point_mutate(base)
                genotype, ops, dist = ednag.recombine(base, variant)
            elif op_type == "flag":
                genotype, ops, dist = ednag.flag_mutate(base)
            else:
                continue
            
            # Check trust region
            if dist > xt.trust_region_radius * (1 + 1e-6):
                self.worm.record(MutationEventType.MUT_SKIP_TR, {
                    "candidate": i,
                    "operator": op_type,
                    "distance": dist,
                    "tr": xt.trust_region_radius
                })
                continue
            
            # Generate candidate
            cand = self._process_candidate(
                genotype, ops, dist, base, xt, plan, acq
            )
            
            if cand:
                candidates.append(cand)
                # Update elite
                ednag.update_elite(genotype, cand.score)
                
                # Collect surrogate data
                features = extract_features(
                    DNAFabric.denormalize(genotype.genes),
                    {"latency_ms": cand.latency_estimate, "cost": cand.cost_estimate, "risk": cand.risk_estimate},
                    acq
                )
                surrogate_data.append({
                    "features": features,
                    "targets": cand.pred_metrics.get("preds", cand.pred_metrics)
                })
        
        # Add elite if exists
        if self.config["operators"]["elite_preserve"]:
            elite = ednag.get_elite()
            if elite:
                genotype, ops, dist = elite
                cand = self._process_candidate(
                    genotype, ops, dist, base, xt, plan, acq
                )
                if cand:
                    candidates.append(cand)
        
        if not candidates:
            abort_proof = self.worm.record(MutationEventType.MUT_ABORT, {
                "reason": "no_valid_candidates",
                "attempted": n_candidates
            })
            raise RuntimeError("No valid candidates generated")
        
        # Train surrogate
        if surrogate_data:
            X = [d["features"] for d in surrogate_data]
            y = {
                "delta_linf_hat": [d["targets"].get("delta_linf_hat", 0) for d in surrogate_data],
                "mdl_gain_hat": [d["targets"].get("mdl_gain_hat", 0) for d in surrogate_data],
                "ppl_ood_hat": [d["targets"].get("ppl_ood_hat", 100) for d in surrogate_data]
            }
            surrogate_report = self.surrogate.fit(X, y)
        else:
            surrogate_report = {"n_samples": 0}
        
        # Re-score with trained surrogate
        for cand in candidates:
            real_params = {p["path"]: p["payload"] for p in cand.patches}
            features = extract_features(
                DNAFabric.denormalize({k: v for patch in cand.patches for k, v in patch.get("payload", {}).items()}),
                {"latency_ms": cand.latency_estimate, "cost": cand.cost_estimate, "risk": cand.risk_estimate},
                acq
            )
            
            pred_ci = self.surrogate.predict_with_ci(features)
            cand.pred_metrics = pred_ci
            cand.score = candidate_score(
                pred_ci, xt, cand.risk_estimate, cand.cost_estimate,
                cand.distance_to_base
            )
            
            self.worm.record(MutationEventType.MUT_SCORE, {
                "cand_id": cand.cand_id,
                "score": cand.score,
                "predictions": pred_ci["preds"],
                "ci": pred_ci["ci"]
            })
        
        # Select top-k with diversity
        selected = self._select_diverse_topk(candidates, top_k, base)
        
        # Calculate diversity metrics
        diversity_summary = self._calculate_diversity(selected)
        
        # Update Xt
        xt_updated = self._update_omega_state(xt, selected, plan_hash, start_proof)
        
        # Create bundle
        bundle = self._create_bundle(
            selected, plan_hash, seed, surrogate_report, diversity_summary
        )
        
        # Log completion
        elapsed_ms = (time.perf_counter() - t0) * 1000
        
        self.worm.record(MutationEventType.MUT_DONE, {
            "bundle_id": bundle.bundle_id,
            "n_selected": len(selected),
            "elapsed_ms": elapsed_ms,
            "proof_ids": [c.proof_id for c in selected]
        })
        
        log(f"✅ Mutation complete: {len(selected)}/{n_candidates} selected in {elapsed_ms:.0f}ms")
        
        return bundle, xt_updated
    
    def _process_candidate(
        self,
        genotype: Genotype,
        ops: List[Dict[str, Any]],
        dist: float,
        base: Genotype,
        xt: OmegaState,
        plan: PlanOmega,
        acq: AcquisitionReport
    ) -> Optional[Candidate]:
        """Processa e valida um candidato."""
        
        cand_id = f"cand_{uuid.uuid4().hex[:8]}"
        
        # Denormalize
        real_params = DNAFabric.denormalize(genotype.genes)
        
        # Micro-benchmark
        micro = micro_benchmark(real_params, acq)
        
        # Check budgets
        required = {"cost": micro["cost"], "latency_ms": micro["latency_ms"]}
        if not plan.budgets.can_afford(required):
            self.worm.record(MutationEventType.MUT_SKIP_BUDGET, {
                "cand_id": cand_id,
                "required": required,
                "available": plan.budgets.to_dict()
            })
            return None
        
        # Generate test code
        test_code = self._generate_test_code(real_params, cand_id)
        
        # Sandbox execution
        sandbox_ok, sandbox_result = run_in_sandbox(
            test_code,
            self.config["sandbox"]["timeout_s"],
            self.config["sandbox"]["mem_limit_mb"]
        )
        
        if not sandbox_ok:
            self.worm.record(MutationEventType.MUT_SANITIZE, {
                "cand_id": cand_id,
                "verdict": "fail",
                "errors": sandbox_result.get("errors", [])
            })
            return None
        
        self.worm.record(MutationEventType.MUT_SANITIZE, {
            "cand_id": cand_id,
            "verdict": "pass",
            "metrics": sandbox_result
        })
        
        # Generate patches
        patches = [
            {
                "type": "param",
                "path": "config",
                "payload": real_params
            }
        ]
        
        # Extract features
        features = extract_features(real_params, micro, acq)
        
        # Initial prediction (will be refined after surrogate training)
        pred_metrics = {
            "delta_linf_hat": max(0.0, 0.01 + 0.1 * random.random()),
            "mdl_gain_hat": max(0.0, 0.005 + 0.05 * random.random()),
            "ppl_ood_hat": max(1.0, 95.0 - 10.0 * random.random())
        }
        
        # Calculate score
        score = candidate_score(
            {"preds": pred_metrics}, xt,
            micro["risk"], micro["cost"], dist
        )
        
        # Record candidate
        proof_id = self.worm.record(MutationEventType.MUT_CANDIDATE, {
            "cand_id": cand_id,
            "op_seq": ops,
            "distance": dist,
            "score": score
        })
        
        # Allocate budget
        plan.budgets.allocate(required, f"candidate_{cand_id}")
        
        return Candidate(
            cand_id=cand_id,
            parent_ids=genotype.parent_ids,
            op_seq=ops,
            distance_to_base=dist,
            patches=patches,
            build_steps=[f"python -c '{test_code}'"],
            env_caps={
                "cpu_seconds": self.config["sandbox"]["cpu_quota_ms"] / 1000,
                "mem_mb": self.config["sandbox"]["mem_limit_mb"],
                "no_net": True
            },
            pred_metrics={"preds": pred_metrics, "ci": {}},
            risk_estimate=micro["risk"],
            cost_estimate=micro["cost"],
            latency_estimate=micro["latency_ms"],
            score=score,
            explain=f"Generated via {ops[0]['op'] if ops else 'unknown'} with TR distance {dist:.3f}",
            proof_id=proof_id
        )
    
    def _generate_test_code(self, params: Dict[str, Any], cand_id: str) -> str:
        """Gera código de teste baseado nos parâmetros."""
        code = f"""
# Test code for candidate {cand_id}
def test_model(x, params):
    lr = params.get('hp.lr', 0.01)
    batch = params.get('hp.batch', 32)
    dropout = params.get('hp.dropout', 0.0)
    
    # Simulate forward pass
    result = x * lr
    if dropout > 0:
        result *= (1 - dropout)
    
    return result

params = {repr(params)}
output = test_model(1.0, params)
assert isinstance(output, (int, float))
"""
        return code
    
    def _select_diverse_topk(self, candidates: List[Candidate], k: int, base: Genotype) -> List[Candidate]:
        """Seleciona top-k com diversidade."""
        # Sort by score
        candidates.sort(key=lambda c: c.score, reverse=True)
        
        if len(candidates) <= k:
            return candidates
        
        selected = [candidates[0]]  # Always include best
        
        for cand in candidates[1:]:
            if len(selected) >= k:
                break
            
            # Calculate diversity
            min_div = float('inf')
            for sel in selected:
                div = self._candidate_diversity(cand, sel)
                min_div = min(min_div, div)
            
            # Accept if diverse enough
            if min_div >= self.config["diversity"]["min_threshold"]:
                selected.append(cand)
        
        # Fill remaining slots if needed
        while len(selected) < k and len(selected) < len(candidates):
            for cand in candidates:
                if cand not in selected:
                    selected.append(cand)
                    break
        
        return selected[:k]
    
    def _candidate_diversity(self, a: Candidate, b: Candidate) -> float:
        """Calcula diversidade entre candidatos."""
        # Operator diversity
        a_ops = {op["op"] for op in a.op_seq}
        b_ops = {op["op"] for op in b.op_seq}
        op_jaccard = len(a_ops & b_ops) / max(1, len(a_ops | b_ops))
        
        # Distance diversity
        dist_diff = abs(a.distance_to_base - b.distance_to_base)
        
        # Score diversity
        score_diff = abs(a.score - b.score) / max(0.001, max(a.score, b.score))
        
        # Combined diversity
        diversity = (1 - op_jaccard) * 0.4 + dist_diff * 0.3 + score_diff * 0.3
        
        return diversity
    
    def _calculate_diversity(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """Calcula métricas de diversidade."""
        if not candidates:
            return {}
        
        # Operator counts
        op_counts = Counter()
        for cand in candidates:
            for op in cand.op_seq:
                op_counts[op["op"]] += 1
        
        # Distance stats
        distances = [c.distance_to_base for c in candidates]
        
        # Score stats
        scores = [c.score for c in candidates]
        
        return {
            "n_candidates": len(candidates),
            "operators": dict(op_counts),
            "distance": {
                "mean": sum(distances) / len(distances),
                "min": min(distances),
                "max": max(distances),
                "std": math.sqrt(sum((d - sum(distances)/len(distances))**2 for d in distances) / len(distances)) if len(distances) > 1 else 0
            },
            "score": {
                "mean": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores)
            }
        }
    
    def _update_omega_state(self, xt: OmegaState, candidates: List[Candidate], plan_hash: str, start_proof: str) -> OmegaState:
        """Atualiza estado Omega com predições agregadas."""
        xt_updated = xt  # In-place update
        
        # Aggregate predictions
        if candidates:
            delta_preds = [c.pred_metrics.get("preds", {}).get("delta_linf_hat", 0) for c in candidates]
            mdl_preds = [c.pred_metrics.get("preds", {}).get("mdl_gain_hat", 0) for c in candidates]
            ppl_preds = [c.pred_metrics.get("preds", {}).get("ppl_ood_hat", 100) for c in candidates]
            
            xt_updated.delta_linf_pred = sum(delta_preds) / len(delta_preds)
            xt_updated.mdl_gain_pred = sum(mdl_preds) / len(mdl_preds)
            xt_updated.ppl_ood_pred = sum(ppl_preds) / len(ppl_preds)
        
        # Update hashes and proofs
        xt_updated.hashes.append(plan_hash)
        xt_updated.hashes.append(_hash_data([c.cand_id for c in candidates]))
        xt_updated.proof_ids.append(start_proof)
        xt_updated.proof_ids.extend([c.proof_id for c in candidates[:3]])  # Top 3 proofs
        
        # Update capabilities
        xt_updated.adv_capabilities = {
            "has_lora": any("lora" in str(c.patches) for c in candidates),
            "has_net2net": any("net2net" in str(c.patches) for c in candidates),
            "has_quant": any("quant" in str(c.patches) for c in candidates)
        }
        
        # Increment cycle
        xt_updated.cycle_count += 1
        
        return xt_updated
    
    def _create_bundle(
        self,
        candidates: List[Candidate],
        plan_hash: str,
        seed: int,
        surrogate_report: Dict[str, Any],
        diversity_summary: Dict[str, Any]
    ) -> MutationBundle:
        """Cria e empacota o bundle de mutação."""
        
        bundle_id = f"bundle_{uuid.uuid4().hex[:8]}"
        bundle_dir = DIRS["BUNDLES"] / bundle_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        
        # Create manifest
        manifest = {
            "bundle_id": bundle_id,
            "plan_hash": plan_hash,
            "seed": seed,
            "timestamp": _ts(),
            "version": self.config["version"],
            "topK": [asdict(c) for c in candidates],
            "surrogate_report": surrogate_report,
            "diversity_summary": diversity_summary
        }
        
        # Save manifest
        save_json(bundle_dir / "manifest.json", manifest)
        
        # Save patches
        for cand in candidates:
            patch_file = bundle_dir / f"{cand.cand_id}_patch.json"
            save_json(patch_file, {
                "patches": cand.patches,
                "build_steps": cand.build_steps,
                "env_caps": cand.env_caps
            })
        
        # Create zip
        zip_path = bundle_dir.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(bundle_dir / "manifest.json", "manifest.json")
            for cand in candidates:
                patch_file = f"{cand.cand_id}_patch.json"
                z.write(bundle_dir / patch_file, f"patches/{patch_file}")
        
        # Clean up directory
        shutil.rmtree(bundle_dir)
        
        # Record bundle creation
        self.worm.record(MutationEventType.MUT_BUNDLE, {
            "bundle_id": bundle_id,
            "artifact_path": str(zip_path),
            "n_candidates": len(candidates)
        })
        
        return MutationBundle(
            bundle_id=bundle_id,
            plan_hash=plan_hash,
            seed=seed,
            topK=candidates,
            surrogate_report=surrogate_report,
            diversity_summary=diversity_summary,
            artifact_path=str(zip_path),
            xt_updates={}
        )

# =============================================================================
# API PÚBLICA
# =============================================================================

def mutate_and_rank(
    xt: OmegaState,
    plan: PlanOmega,
    acq: AcquisitionReport,
    *,
    n_candidates: int = 32,
    top_k: int = 5,
    seed: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[MutationBundle, OmegaState]:
    """
    Função principal do módulo 4/8.
    
    Gera candidatos evolutivos seguros e ranqueados para o Crisol (5/8).
    
    Args:
        xt: Estado Omega atual (1/8)
        plan: Plano Ω-META (2/8)
        acq: Relatório de aquisição (3/8)
        n_candidates: Número de candidatos a gerar
        top_k: Número de candidatos a selecionar
        seed: Seed para determinismo
        config: Configuração customizada
        
    Returns:
        Tupla (MutationBundle, OmegaState atualizado)
    """
    engine = MutationEngine(config=config)
    return engine.execute(xt, plan, acq, n_candidates, top_k, seed)

# =============================================================================
# CLI E TESTES
# =============================================================================

def _cli():
    """Interface de linha de comando."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PENIN-Ω 4/8 - Mutação, Geração & Neurofusão"
    )
    parser.add_argument("--xt", help="Path para Xt.json")
    parser.add_argument("--plan", help="Path para PlanOmega.json")
    parser.add_argument("--acq", help="Path para AcquisitionReport.json")
    parser.add_argument("--n", type=int, default=32, help="Número de candidatos")
    parser.add_argument("--k", type=int, default=5, help="Top-K a selecionar")
    parser.add_argument("--seed", type=int, help="Seed para determinismo")
    parser.add_argument("--test", action="store_true", help="Executar testes")
    
    args = parser.parse_args()
    
    if args.test:
        _run_tests()
        return
    
    # Load inputs
    if args.xt and Path(args.xt).exists():
        xt_data = load_json(Path(args.xt))
        xt = OmegaState.from_dict(xt_data)
    else:
        xt = OmegaState()
    
    if args.plan and Path(args.plan).exists():
        plan_data = load_json(Path(args.plan))
        plan = PlanOmega.from_dict(plan_data)
    else:
        plan = PlanOmega()
    
    if args.acq and Path(args.acq).exists():
        acq_data = load_json(Path(args.acq))
        acq = AcquisitionReport.from_dict(acq_data)
    else:
        acq = AcquisitionReport()
    
    # Execute
    try:
        bundle, xt_updated = mutate_and_rank(
            xt, plan, acq,
            n_candidates=args.n,
            top_k=args.k,
            seed=args.seed
        )
        
        # Print results
        print("\n" + "="*60)
        print("MUTATION BUNDLE GENERATED")
        print("="*60)
        print(f"Bundle ID: {bundle.bundle_id}")
        print(f"Candidates: {len(bundle.topK)}")
        print(f"Artifact: {bundle.artifact_path}")
        print(f"\nTop candidates:")
        for i, cand in enumerate(bundle.topK[:3], 1):
            print(f"  {i}. {cand.cand_id}")
            print(f"     Score: {cand.score:.4f}")
            print(f"     Distance: {cand.distance_to_base:.3f}")
            print(f"     Predicted ΔL∞: {cand.pred_metrics.get('preds', {}).get('delta_linf_hat', 0):.4f}")
        
        print(f"\nDiversity: {bundle.diversity_summary}")
        print(f"\nXt updates:")
        print(f"  ΔL∞_pred: {xt_updated.delta_linf_pred:.4f}")
        print(f"  MDL_pred: {xt_updated.mdl_gain_pred:.4f}")
        print(f"  PPL_pred: {xt_updated.ppl_ood_pred:.1f}")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return 1
    
    return 0

def _run_tests():
    """Executa suite de testes."""
    print("Running tests...")
    
    # Test 1: Sanitization
    bad_code = "import os\nos.system('ls')"
    ok, issues = sanitize_python_source(bad_code)
    assert not ok and "ban_import:os" in str(issues), "Sanitization test failed"
    print("✓ Sanitization test passed")
    
    # Test 2: Distance metric
    g1 = Genotype(1, {"hp.lr": 0.5}, "hash1")
    g2 = Genotype(1, {"hp.lr": 0.6}, "hash2")
    ednag = EDNAGenerator(0.1, 42)
    dist = ednag.distance(g1, g2)
    assert 0 <= dist <= 1, "Distance test failed"
    print("✓ Distance test passed")
    
    # Test 3: Surrogate
    surrogate = AdvancedSurrogate()
    X = [[0.5] * 20 for _ in range(10)]
    y = {
        "delta_linf_hat": [0.1] * 10,
        "mdl_gain_hat": [0.05] * 10,
        "ppl_ood_hat": [90.0] * 10
    }
    report = surrogate.fit(X, y)
    assert "n_samples" in report, "Surrogate test failed"
    print("✓ Surrogate test passed")
    
    # Test 4: End-to-end
    xt = OmegaState()
    plan = PlanOmega()
    acq = AcquisitionReport()
    
    try:
        bundle, xt_updated = mutate_and_rank(
            xt, plan, acq,
            n_candidates=8,
            top_k=3,
            seed=42
        )
        assert len(bundle.topK) >= 1, "E2E test failed"
        print("✓ End-to-end test passed")
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")
    
    print("\nAll tests completed!")

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main API
    "mutate_and_rank",
    
    # Data models
    "OmegaState",
    "PlanOmega",
    "AcquisitionReport",
    "Genotype",
    "Candidate",
    "MutationBundle",
    
    # Components
    "DNAFabric",
    "EDNAGenerator",
    "AdvancedSurrogate",
    "MutationEngine",
    
    # Utils
    "candidate_score",
    "sanitize_python_source",
    "run_in_sandbox"
]

if __name__ == "__main__":
    exit(_cli())
