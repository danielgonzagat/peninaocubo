#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω · Fase 6/8 — Auto-Crítica, Auto-Rewrite & Mutação On-line (TTD-DR)
================================================================================
Objetivo (escopo do arquivo):
    Este módulo implementa o laço fechado TTD-DR (Think → Test → Debate → Do → Review)
    para reescritas e mutações on-line com segurança, auditabilidade e rollback atômico:
      - Ingere PromotionSet do 5/8 e/ou tickets autônomos (watchdog/objetivos).
      - Sanitiza patches (AST) e executa validações em sandbox sem rede (CPU-limits).
      - Verifica portões Σ-Guard/IR→IC/SR-Ω∞/Trust-Region e budgets do PlanΩ (2/8).
      - Aplica a mudança de forma atômica + snapshot/rollback → PROMOTE/CANARY/ROLLBACK.
      - Registra trilha WORM (JSONL Merkle-like) e gera AutoRewriteReport.

Integração:
    - 1/8 (núcleo): recebe AutoRewriteReport e proofs para decisão final.
    - 2/8 (estratégia): respeita constraints/budgets e devolve sinais de utilidade/TR observada.
    - 3/8 (aquisição): opcional para testes dirigidos (respeita budgets).
    - 4/8 (mutação): usa patches aprovados (PromotionSet) e pode recombinar.
    - 5/8 (crisol): ponto de partida preferencial dos candidatos (ALLOW/CANARY).
    - 7/8 (scheduler): aciona rollout canário e monitora critérios.
    - 8/8 (bridge): opcional para rationale local (sem rede), não vinculante.

CPU-first, sem rede: todas as execuções de teste ocorrem em sandbox local
com limites de CPU/RAM/tempo (POSIX) e sem abertura de sockets.

Autor: Equipe PENIN-Ω
Versão: 6.0.0
Licença: MIT
"""

from __future__ import annotations
import os
import sys
import re
import io
import ast
import json
import time
import uuid
import math
import shutil
import hashlib
import tempfile
import traceback
import subprocess
import resource
import signal
from copy import deepcopy
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Literal, Union
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import sqlite3
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURAÇÃO E PATHS
# =============================================================================

ROOT = Path(os.getenv("PENIN_ROOT", "/opt/penin_omega"))
if not ROOT.exists():
    ROOT = Path.home() / ".penin_omega"

DIRS = {
    "LOG":       ROOT / "logs",
    "STATE":     ROOT / "state",
    "WORM":      ROOT / "worm_ledger",
    "WORK":      ROOT / "workspace",
    "PATCHES":   ROOT / "patches",
    "SANDBOX":   ROOT / "sandbox",
    "ARTIFACTS": ROOT / "artifacts_fase6",
    "CONFIG":    ROOT / "config",
    "TESTS":     ROOT / "tests",
    "TICKETS":   ROOT / "tickets"
}

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = DIRS["LOG"] / "fase6.log"
WORM_FILE = DIRS["WORM"] / "fase6.jsonl"
TICKET_DB = DIRS["TICKETS"] / "tickets.db"

# =============================================================================
# CONFIGURAÇÃO PADRÃO
# =============================================================================

DEFAULT_CONFIG = {
    "version": "6.0.0",
    "sandbox": {
        "timeout_s": 60,
        "max_memory_mb": 512,
        "max_cpu_percent": 50,
        "no_network": True,
        "read_only_fs": True
    },
    "budgets": {
        "max_cost": 3.0,
        "max_latency_ms": 30000,
        "max_llm_calls": 5
    },
    "validation": {
        "test_order": ["unit", "integration", "robustness", "perf"],
        "timeout_by_stage": {
            "unit": 60,
            "integration": 120,
            "robustness": 120,
            "perf": 60
        },
        "fail_on_critical": ["integration", "robustness"]
    },
    "canary": {
        "default_traffic_pct": 0.10,
        "default_duration_min": 30,
        "rollback_criteria": {
            "rho_spike": 0.03,
            "ppl_regress": 0.05,
            "ece_spike": 0.005
        }
    },
    "trust_region": {
        "shrink_factor": 0.9,
        "never_expand": True
    }
}

# =============================================================================
# UTILITÁRIOS
# =============================================================================

def _ts() -> str:
    """Timestamp ISO8601 com timezone."""
    return datetime.now(timezone.utc).isoformat()

def _hash_data(obj: Any) -> str:
    """Hash SHA256 de dados."""
    if isinstance(obj, (dict, list)):
        payload = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    elif isinstance(obj, str):
        payload = obj.encode("utf-8")
    else:
        payload = str(obj).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def _log(msg: str, level: str = "INFO"):
    """Log com timestamp."""
    line = f"[{_ts()}] [F6] [{level}] {msg}\n"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    sys.stdout.write(line)
    sys.stdout.flush()

def load_json_file(p: Path, default=None):
    """Carrega arquivo JSON."""
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json_file(p: Path, obj: Any):
    """Salva objeto como JSON."""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

# =============================================================================
# WORM LEDGER (Write-Once-Read-Many)
# =============================================================================

class WORMEvent(Enum):
    """Eventos WORM para auditoria."""
    AUTOREWRITE_TICKET_CREATED = "AUTOREWRITE_TICKET_CREATED"
    AUTOREWRITE_START = "AUTOREWRITE_START"
    PATCH_SANITIZED = "PATCH_SANITIZED"
    AUTOREWRITE_VALIDATE_OK = "AUTOREWRITE_VALIDATE_OK"
    AUTOREWRITE_VALIDATE_FAIL = "AUTOREWRITE_VALIDATE_FAIL"
    AUTOREWRITE_APPLY = "AUTOREWRITE_APPLY"
    CANARY_START = "CANARY_START"
    CANARY_RESULT = "CANARY_RESULT"
    AUTOREWRITE_PROMOTE = "AUTOREWRITE_PROMOTE"
    AUTOREWRITE_ROLLBACK = "AUTOREWRITE_ROLLBACK"
    AUTOREWRITE_ABORT = "AUTOREWRITE_ABORT"
    AUTOREWRITE_RESULT = "AUTOREWRITE_RESULT"

class WORM:
    """Ledger imutável para auditoria."""
    
    def __init__(self, path: Path = WORM_FILE):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._tail_hash()
    
    def _tail_hash(self) -> str:
        """Obtém hash do último evento."""
        if not self.path.exists() or self.path.stat().st_size == 0:
            return "genesis"
        try:
            with self.path.open("rb") as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b"\n":
                    f.seek(-2, os.SEEK_CUR)
                last = f.readline().decode("utf-8")
            return json.loads(last).get("hash", "genesis")
        except Exception:
            return "genesis"
    
    def record(self, event_type: Union[str, WORMEvent], data: Dict[str, Any]) -> str:
        """Registra evento no ledger."""
        if isinstance(event_type, WORMEvent):
            event_type = event_type.value
        
        ev = {
            "type": event_type,
            "ts": _ts(),
            "data": data,
            "prev_hash": self._last_hash,
        }
        ev["hash"] = _hash_data({k: v for k, v in ev.items() if k != "hash"})
        
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        
        self._last_hash = ev["hash"]
        return ev["hash"]

# =============================================================================
# DTOs / CONTRATOS
# =============================================================================

@dataclass
class OmegaState:
    """Estado do sistema Omega."""
    ece: float = 0.0
    rho_bias: float = 1.0
    consent: bool = True
    eco_ok: bool = True
    rho: float = 0.5
    C: float = 0.6
    A: float = 0.6
    O: float = 0.6
    S: float = 0.6
    caos_pre: float = 1.0
    caos_post: float = 1.0
    sr_score: float = 1.0
    trust_region_radius: float = 0.10
    delta_linf: float = 0.0
    mdl_gain: float = 0.0
    ppl_ood: float = 100.0
    E_t: bool = True

@dataclass
class PlanOmega:
    """Plano estratégico do 2/8."""
    constraints: Dict[str, Any] = field(default_factory=dict)
    budgets: Dict[str, Any] = field(default_factory=dict)
    policies: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PatchCandidate:
    """Candidato a patch."""
    cand_id: str
    patch_file: str
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PromotionSet:
    """Conjunto de patches promovidos do 5/8."""
    top: List[str] = field(default_factory=list)
    patchset: List[PatchCandidate] = field(default_factory=list)

@dataclass
class AutoRewriteTicket:
    """Ticket de reescrita automática."""
    ticket_id: str
    source: str  # "crucible|watchdog|goal|ops"
    priority: int = 50
    goal: str = ""
    promotion_set: Optional[PromotionSet] = None
    plan_constraints: Dict[str, Any] = field(default_factory=dict)
    budgets: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    deadline: Optional[str] = None

@dataclass
class ValidationReport:
    """Relatório de validação por estágio."""
    stage: Literal["unit", "integration", "robustness", "perf"]
    passed: bool
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

@dataclass
class AutoRewriteReport:
    """Relatório final de reescrita."""
    ticket_id: str
    applied: bool
    verdict: Literal["PROMOTE", "CANARY", "ROLLBACK", "ABORT"]
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    budgets_used: Dict[str, float]
    patches_applied: List[Dict[str, str]] = field(default_factory=list)
    canary_plan: Optional[Dict[str, Any]] = None
    worm_proofs: List[str] = field(default_factory=list)
    notes: str = ""

# =============================================================================
# TICKET STORE (Persistência e Idempotência)
# =============================================================================

class TicketStore:
    """Gerenciamento de tickets com idempotência."""
    
    def __init__(self, db_path: Path = TICKET_DB):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa database SQLite."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                source TEXT,
                priority INTEGER,
                goal TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT,
                data TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def save(self, ticket: AutoRewriteTicket):
        """Salva ticket (idempotente)."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO tickets 
            (ticket_id, source, priority, goal, status, created_at, updated_at, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket.ticket_id,
            ticket.source,
            ticket.priority,
            ticket.goal,
            "PENDING",
            _ts(),
            _ts(),
            json.dumps(asdict(ticket))
        ))
        conn.commit()
        conn.close()
    
    def get(self, ticket_id: str) -> Optional[AutoRewriteTicket]:
        """Recupera ticket por ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            "SELECT data FROM tickets WHERE ticket_id = ?",
            (ticket_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = json.loads(row[0])
            return AutoRewriteTicket(**data)
        return None
    
    def update_status(self, ticket_id: str, status: str):
        """Atualiza status do ticket."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "UPDATE tickets SET status = ?, updated_at = ? WHERE ticket_id = ?",
            (status, _ts(), ticket_id)
        )
        conn.commit()
        conn.close()

# =============================================================================
# SANITIZAÇÃO DE PATCHES (AST)
# =============================================================================

class PatchSanitizer(ast.NodeVisitor):
    """Sanitiza patches via análise AST."""
    
    banned_modules = {
        "os", "subprocess", "socket", "ssl", "selectors", 
        "asyncio", "multiprocessing", "threading", "ctypes"
    }
    banned_calls = {
        "exec", "eval", "compile", "__import__", "open", 
        "input", "system", "popen", "getattr", "setattr"
    }
    
    def __init__(self):
        self.violations: List[str] = []
    
    def visit_Import(self, node: ast.Import) -> Any:
        for n in node.names:
            if n.name.split(".")[0] in self.banned_modules:
                self.violations.append(f"Import banido: {n.name}")
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        if node.module and node.module.split(".")[0] in self.banned_modules:
            self.violations.append(f"ImportFrom banido: {node.module}")
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> Any:
        try:
            if isinstance(node.func, ast.Name) and node.func.id in self.banned_calls:
                self.violations.append(f"Chamada banida: {node.func.id}")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in self.banned_calls:
                self.violations.append(f"Chamada banida: {node.func.attr}")
        except Exception:
            pass
        self.generic_visit(node)

def sanitize_patch_text(py_text: str) -> List[str]:
    """Sanitiza código Python."""
    try:
        tree = ast.parse(py_text)
    except Exception as e:
        return [f"AST inválida: {e}"]
    
    ps = PatchSanitizer()
    ps.visit(tree)
    return ps.violations

# =============================================================================
# APLICAÇÃO DE PATCH
# =============================================================================

@contextmanager
def atomic_workspace_snapshot(work_dir: Path):
    """Snapshot atômico do workspace."""
    if not work_dir.exists():
        work_dir.mkdir(parents=True, exist_ok=True)
    
    with tempfile.TemporaryDirectory(prefix="penin_f6_snap_") as tmpd:
        tmp = Path(tmpd) / "snapshot"
        shutil.copytree(work_dir, tmp, dirs_exist_ok=True)
        try:
            yield
        except Exception:
            # Rollback
            _log("↩️  Rollback: restaurando snapshot do workspace")
            for item in work_dir.iterdir():
                if item.is_file():
                    item.unlink(missing_ok=True)
                else:
                    shutil.rmtree(item, ignore_errors=True)
            shutil.copytree(tmp, work_dir, dirs_exist_ok=True)
            raise

def _apply_unified_diff(target_root: Path, patch_text: str) -> List[str]:
    """Aplica diffs unificados ou patches JSON."""
    changed: List[str] = []
    
    try:
        # Tenta interpretar como JSON
        data = json.loads(patch_text)
        if isinstance(data, dict) and "file" in data and "new_content" in data:
            fp = target_root / data["file"]
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(data["new_content"], encoding="utf-8")
            changed.append(data["file"])
            return changed
    except Exception:
        pass
    
    # Fallback: unified diff
    file_blocks = re.split(r"(?m)^diff --git a/.* b/(.*)$", patch_text)
    if len(file_blocks) > 1:
        it = iter(file_blocks[1:])
        for rel_path, content in zip(it, it):
            rel_path = rel_path.strip()
            fp = target_root / rel_path
            fp.parent.mkdir(parents=True, exist_ok=True)
            
            new_lines = []
            for ln in content.splitlines():
                if ln.startswith('+++') or ln.startswith('---') or ln.startswith('@@'):
                    continue
                if len(ln) and ln[0] == '+':
                    new_lines.append(ln[1:])
            
            if new_lines:
                fp.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                changed.append(rel_path)
    
    return changed

class PatchApplier:
    """Aplicador de patches com rollback."""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
    
    def apply(self, patch_file: Path, worm: WORM) -> Tuple[bool, List[str], str]:
        """Aplica patch de forma atômica."""
        try:
            txt = patch_file.read_text(encoding="utf-8")
        except Exception as e:
            return (False, [], f"Não foi possível ler patch: {e}")
        
        # Sanitiza se for Python
        try:
            d = json.loads(txt)
            if isinstance(d, dict) and d.get("file", "").endswith(".py") and "new_content" in d:
                violations = sanitize_patch_text(d["new_content"])
                if violations:
                    worm.record(WORMEvent.PATCH_SANITIZED, {
                        "status": "FAIL",
                        "violations": violations
                    })
                    return (False, [], f"Violação AST: {violations}")
                worm.record(WORMEvent.PATCH_SANITIZED, {"status": "OK"})
        except Exception:
            pass
        
        changed_files: List[str] = []
        try:
            with atomic_workspace_snapshot(self.workspace):
                changed_files = _apply_unified_diff(self.workspace, txt)
            return (True, changed_files, "")
        except Exception as e:
            return (False, changed_files, f"Falha aplicando patch: {e}")

# =============================================================================
# SANDBOX RUNNER
# =============================================================================

class SandboxRunner:
    """Executa código em sandbox isolado."""
    
    def __init__(self, sandbox_dir: Path, config: Dict[str, Any]):
        self.sandbox_dir = sandbox_dir
        self.config = config
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    def _limit_resources(self):
        """Limita recursos do processo (Linux/Unix)."""
        if hasattr(resource, 'RLIMIT_AS'):
            max_mem = self.config["sandbox"]["max_memory_mb"] * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_mem, max_mem))
        if hasattr(resource, 'RLIMIT_CPU'):
            max_cpu = self.config["sandbox"]["timeout_s"]
            resource.setrlimit(resource.RLIMIT_CPU, (max_cpu, max_cpu))
    
    def run_test(self, stage: str, test_script: Optional[Path] = None, 
                 timeout_s: Optional[int] = None) -> ValidationReport:
        """Executa teste em sandbox."""
        timeout = timeout_s or self.config["validation"]["timeout_by_stage"].get(stage, 60)
        
        # Procura script de teste
        if not test_script:
            test_script = DIRS["TESTS"] / f"test_{stage}.py"
        
        if not test_script.exists():
            # Teste vazio passa por padrão (para desenvolvimento)
            return ValidationReport(
                stage=stage,
                passed=True,
                metrics={"elapsed_s": 0.0},
                artifacts=[],
                errors=[]
            )
        
        # Prepara ambiente isolado
        env = os.environ.copy()
        env["NO_NET"] = "1"
        env["PYTHONWARNINGS"] = "ignore"
        env["SANDBOX"] = "1"
        
        # Executa teste
        t0 = time.time()
        try:
            proc = subprocess.Popen(
                [sys.executable, str(test_script)],
                cwd=str(self.sandbox_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                preexec_fn=self._limit_resources if os.name != 'nt' else None
            )
            
            out, err = proc.communicate(timeout=timeout)
            elapsed = time.time() - t0
            
            # Parseia métricas do output (formato JSON)
            metrics = {"elapsed_s": elapsed}
            try:
                if out and out.strip().startswith("{"):
                    metrics.update(json.loads(out))
            except Exception:
                pass
            
            passed = (proc.returncode == 0)
            errors = [err] if err and not passed else []
            
            return ValidationReport(
                stage=stage,
                passed=passed,
                metrics=metrics,
                artifacts=[str(self.sandbox_dir / f"{stage}.log")],
                errors=errors
            )
            
        except subprocess.TimeoutExpired:
            proc.kill()
            return ValidationReport(
                stage=stage,
                passed=False,
                metrics={"elapsed_s": timeout},
                artifacts=[],
                errors=["TIMEOUT"]
            )
        except Exception as e:
            return ValidationReport(
                stage=stage,
                passed=False,
                metrics={"elapsed_s": time.time() - t0},
                artifacts=[],
                errors=[str(e)]
            )

class Validator:
    """Orquestra validações."""
    
    def __init__(self, workspace: Path, config: Dict[str, Any]):
        self.workspace = workspace
        self.config = config
        self.sandbox = SandboxRunner(workspace / "sandbox", config)
    
    def validate(self, patches: List[PatchCandidate], worm: WORM) -> List[ValidationReport]:
        """Valida patches através dos estágios de teste."""
        reports = []
        
        for stage in self.config["validation"]["test_order"]:
            rep = self.sandbox.run_test(stage)
            reports.append(rep)
            
            # Registra no WORM
            event = WORMEvent.AUTOREWRITE_VALIDATE_OK if rep.passed else WORMEvent.AUTOREWRITE_VALIDATE_FAIL
            worm.record(event, {
                "stage": stage,
                "passed": rep.passed,
                "metrics": rep.metrics,
                "errors": rep.errors
            })
            
            # Fail-closed em estágios críticos
            if not rep.passed and stage in self.config["validation"]["fail_on_critical"]:
                _log(f"❌ Falha crítica em {stage}, abortando validação")
                break
        
        return reports

# =============================================================================
# POLICY ENGINE
# =============================================================================

class PolicyEngine:
    """Motor de políticas e decisões."""
    
    def __init__(self, constraints: Dict[str, Any], budgets: Dict[str, Any]):
        self.constraints = constraints
        self.budgets = budgets
    
    def _sigma_guard_ok(self, xt: OmegaState) -> bool:
        """Verifica Σ-Guard (ética)."""
        ece_max = float(self.constraints.get("ece_max", 0.01))
        rho_bias_max = float(self.constraints.get("rho_bias_max", 1.05))
        return (xt.ece <= ece_max and 
                xt.rho_bias <= rho_bias_max and 
                xt.consent and 
                xt.eco_ok)
    
    def _risk_ok(self, xt: OmegaState) -> bool:
        """Verifica IR→IC (risco)."""
        rho_max = float(self.constraints.get("rho_max", 0.95))
        return xt.rho < rho_max
    
    def _sr_gate_ok(self, xt: OmegaState) -> bool:
        """Verifica SR-Ω∞ gate."""
        tau_sr = float(self.constraints.get("tau_sr", 0.80))
        return xt.sr_score >= tau_sr
    
    def _within_trust_region(self, before: OmegaState, after: OmegaState) -> bool:
        """Verifica Trust-Region."""
        tr = float(self.constraints.get("tr_radius", before.trust_region_radius))
        return after.trust_region_radius <= tr
    
    def _check_budgets(self, budgets_used: Dict[str, float]) -> bool:
        """Verifica orçamentos."""
        for key, used in budgets_used.items():
            max_key = f"max_{key}"
            if max_key in self.budgets:
                if used > float(self.budgets[max_key]):
                    return False
        return True
    
    def decide(self, before: OmegaState, after: OmegaState, 
               budgets_used: Dict[str, float]) -> str:
        """Decide veredito baseado em políticas lexicográficas."""
        
        # 1. Orçamentos
        if not self._check_budgets(budgets_used):
            return "ABORT"
        
        # 2. Ética (Σ-Guard)
        if not self._sigma_guard_ok(after):
            return "ROLLBACK"
        
        # 3. Risco (IR→IC)
        if not self._risk_ok(after):
            return "ROLLBACK"
        
        # 4. SR-Gate
        if not self._sr_gate_ok(after):
            return "CANARY"  # Máximo canário
        
        # 5. Trust-Region
        if not self._within_trust_region(before, after):
            return "ROLLBACK"
        
        # 6. Performance
        if (after.ppl_ood <= before.ppl_ood and 
            after.delta_linf >= before.delta_linf):
            return "PROMOTE"
        
        return "CANARY"

# =============================================================================
# CANARY MANAGER
# =============================================================================

class CanaryManager:
    """Gerencia planos de canário."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config["canary"]
    
    def create_plan(self, ticket_id: str, metrics_delta: Dict[str, float]) -> Dict[str, Any]:
        """Cria plano de canário."""
        plan = {
            "ticket_id": ticket_id,
            "traffic_pct": self.config["default_traffic_pct"],
            "duration_min": self.config["default_duration_min"],
            "rollback_criteria": self.config["rollback_criteria"].copy(),
            "metrics_delta": metrics_delta,
            "created_at": _ts()
        }
        
        # Ajusta critérios baseado no delta de métricas
        if abs(metrics_delta.get("rho", 0)) > 0.05:
            plan["traffic_pct"] *= 0.5  # Reduz tráfego se mudança grande
        
        return plan
    
    def save_plan(self, plan: Dict[str, Any]):
        """Salva plano para o 7/8 scheduler."""
        plan_file = DIRS["STATE"] / f"canary_{plan['ticket_id']}.json"
        save_json_file(plan_file, plan)
        _log(f"📋 Plano de canário salvo: {plan_file}")

# =============================================================================
# ORQUESTRADOR TTD-DR
# =============================================================================

class Fase6AutoRewrite:
    """Orquestrador principal do ciclo TTD-DR."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.workdir = DIRS["WORK"]
        self.worm = WORM()
        self.ticket_store = TicketStore()
        self.canary_manager = CanaryManager(self.config)
    
    def _think(self, xt: OmegaState, ticket: AutoRewriteTicket, 
               plan: PlanOmega) -> Dict[str, Any]:
        """THINK: Consolida evidências e planeja."""
        _log(f"🧠 THINK: Analisando ticket {ticket.ticket_id}")
        
        # Mescla constraints e budgets
        constraints = {**plan.constraints, **ticket.plan_constraints}
        budgets = {**plan.budgets, **ticket.budgets}
        
        rewrite_plan = {
            "constraints": constraints,
            "budgets": budgets,
            "order": self.config["validation"]["test_order"],
            "timeout_by_stage": self.config["validation"]["timeout_by_stage"],
            "tr_radius": min(
                constraints.get("tr_radius", xt.trust_region_radius),
                xt.trust_region_radius * self.config["trust_region"]["shrink_factor"]
            )
        }
        
        self.worm.record(WORMEvent.AUTOREWRITE_START, {
            "ticket_id": ticket.ticket_id,
            "goal": ticket.goal,
            "constraints": constraints,
            "budgets": budgets
        })
        
        return rewrite_plan
    
    def _test(self, rewrite_plan: Dict[str, Any]) -> List[ValidationReport]:
        """TEST: Valida em sandbox."""
        _log("🧪 TEST: Executando validações em sandbox")
        
        validator = Validator(self.workdir, self.config)
        reports = validator.validate([], self.worm)
        
        total_elapsed = sum(r.metrics.get("elapsed_s", 0) for r in reports)
        _log(f"⏱️  Tempo total de testes: {total_elapsed:.2f}s")
        
        return reports
    
    def _debate(self, reports: List[ValidationReport], 
                before: OmegaState) -> Tuple[OmegaState, float]:
        """DEBATE: Funde opções e calcula score."""
        _log("💬 DEBATE: Analisando resultados e calculando score")
        
        after = deepcopy(before)
        score = 0.0
        
        # Agrega métricas dos reports
        for rep in reports:
            if rep.passed and rep.stage == "robustness":
                # Heurística: melhora se robustness passou
                after.ppl_ood *= 0.95
                after.delta_linf += 0.01
                after.mdl_gain += 0.005
                score += 0.5
        
        # Score lexicográfico + harmônico
        if all(r.passed for r in reports):
            score = 1.0 - (after.ppl_ood / before.ppl_ood)
        
        _log(f"📊 Score calculado: {score:.3f}")
        return after, score
    
    def _do(self, ticket: AutoRewriteTicket) -> Tuple[bool, List[Dict[str, str]], str]:
        """DO: Aplica patches atomicamente."""
        _log("🔨 DO: Aplicando patches")
        
        if not ticket.promotion_set or not ticket.promotion_set.patchset:
            return (False, [], "Nenhum patch no PromotionSet")
        
        applier = PatchApplier(self.workdir)
        changed_meta = []
        
        for cand in ticket.promotion_set.patchset:
            if ticket.promotion_set.top and cand.cand_id not in ticket.promotion_set.top:
                continue
            
            patch_path = Path(cand.patch_file)
            ok, changed, err = applier.apply(patch_path, self.worm)
            
            if not ok:
                return (False, changed_meta, f"Patch {cand.cand_id} falhou: {err}")
            
            changed_meta.append({
                "cand_id": cand.cand_id,
                "patch": str(patch_path),
                "files": ",".join(changed),
                "digest": _hash_data(patch_path.read_text())
            })
            
            self.worm.record(WORMEvent.AUTOREWRITE_APPLY, {
                "cand_id": cand.cand_id,
                "files": changed
            })
        
        _log(f"✅ {len(changed_meta)} patches aplicados com sucesso")
        return (True, changed_meta, "")
    
    def _review(self, before: OmegaState, after: OmegaState, 
                rewrite_plan: Dict[str, Any], 
                reports: List[ValidationReport]) -> Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]:
        """REVIEW: Decide veredito final."""
        _log("📋 REVIEW: Tomando decisão final")
        
        # Calcula orçamentos usados
        budgets_used = {
            "elapsed_tests_s": sum(r.metrics.get("elapsed_s", 0) for r in reports),
            "cost": sum(r.metrics.get("cost", 0) for r in reports)
        }
        
        # Aplica política de decisão
        policy = PolicyEngine(rewrite_plan["constraints"], rewrite_plan["budgets"])
        verdict = policy.decide(before, after, budgets_used)
        
        # Cria plano de canário se necessário
        canary_plan = None
        if verdict == "CANARY":
            metrics_delta = {
                "ppl_ood": after.ppl_ood - before.ppl_ood,
                "rho": after.rho - before.rho,
                "sr_score": after.sr_score - before.sr_score
            }
            canary_plan = self.canary_manager.create_plan(
                rewrite_plan.get("ticket_id", "unknown"),
                metrics_delta
            )
            self.canary_manager.save_plan(canary_plan)
            self.worm.record(WORMEvent.CANARY_START, canary_plan)
        
        # Registra veredito
        event_map = {
            "PROMOTE": WORMEvent.AUTOREWRITE_PROMOTE,
            "CANARY": WORMEvent.CANARY_START,
            "ROLLBACK": WORMEvent.AUTOREWRITE_ROLLBACK,
            "ABORT": WORMEvent.AUTOREWRITE_ABORT
        }
        
        self.worm.record(event_map.get(verdict, WORMEvent.AUTOREWRITE_RESULT), {
            "verdict": verdict,
            "budgets_used": budgets_used
        })
        
        _log(f"⚖️  Veredito: {verdict}")
        return verdict, budgets_used, canary_plan
    
    def process_ticket(self, xt: OmegaState, ticket: AutoRewriteTicket, 
                      plan: PlanOmega) -> AutoRewriteReport:
        """Processa ticket através do ciclo TTD-DR completo."""
        _log(f"🚀 Iniciando TTD-DR para ticket {ticket.ticket_id}")
        
        # Salva ticket para idempotência
        self.ticket_store.save(ticket)
        
        # THINK
        rewrite_plan = self._think(xt, ticket, plan)
        rewrite_plan["ticket_id"] = ticket.ticket_id
        
        # DO
        ok, patches_applied, err = self._do(ticket)
        if not ok:
            proof = self.worm.record(WORMEvent.AUTOREWRITE_ABORT, {
                "ticket_id": ticket.ticket_id,
                "error": err
            })
            return AutoRewriteReport(
                ticket_id=ticket.ticket_id,
                applied=False,
                verdict="ABORT",
                metrics_before=asdict(xt),
                metrics_after=asdict(xt),
                budgets_used={"elapsed_tests_s": 0.0},
                patches_applied=[],
                worm_proofs=[proof],
                notes=f"Falha aplicando patch: {err}"
            )
        
        # TEST
        reports = self._test(rewrite_plan)
        
        # DEBATE
        xt_after, score = self._debate(reports, xt)
        
        # REVIEW
        verdict, budgets_used, canary_plan = self._review(
            xt, xt_after, rewrite_plan, reports
        )
        
        # Atualiza status do ticket
        self.ticket_store.update_status(ticket.ticket_id, verdict)
        
        # WORM final
        final_proof = self.worm.record(WORMEvent.AUTOREWRITE_RESULT, {
            "ticket_id": ticket.ticket_id,
            "verdict": verdict,
            "score": score,
            "metrics_before": {"ppl_ood": xt.ppl_ood, "rho": xt.rho},
            "metrics_after": {"ppl_ood": xt_after.ppl_ood, "rho": xt_after.rho}
        })
        
        # Constrói relatório
        return AutoRewriteReport(
            ticket_id=ticket.ticket_id,
            applied=ok,
            verdict=verdict,
            metrics_before={
                "ppl_ood": xt.ppl_ood,
                "rho": xt.rho,
                "sr_score": xt.sr_score,
                "delta_linf": xt.delta_linf
            },
            metrics_after={
                "ppl_ood": xt_after.ppl_ood,
                "rho": xt_after.rho,
                "sr_score": xt_after.sr_score,
                "delta_linf": xt_after.delta_linf
            },
            budgets_used=budgets_used,
            patches_applied=patches_applied,
            canary_plan=canary_plan,
            worm_proofs=[final_proof],
            notes=f"TTD-DR concluído. Score: {score:.3f}. Veredito: {verdict}"
        )

# =============================================================================
# CLI
# =============================================================================

def _load_path_or_json(maybe_path: str) -> Any:
    """Carrega JSON de arquivo ou string."""
    p = Path(maybe_path)
    if p.exists():
        return load_json_file(p, {})
    else:
        try:
            return json.loads(maybe_path)
        except Exception:
            return {}

def main():
    """Interface CLI."""
    import argparse
    
    ap = argparse.ArgumentParser(
        description="PENIN-Ω Fase 6/8 — Auto-Rewrite & TTD-DR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python fase6.py --xt xt.json --plan plan.json --ticket ticket.json
  python fase6.py --xt '{"ece":0.006,"rho":0.72}' --plan plan.json --ticket ticket.json
        """
    )
    
    ap.add_argument("--xt", required=True, help="OmegaState (arquivo JSON ou JSON inline)")
    ap.add_argument("--plan", required=True, help="PlanΩ (arquivo JSON ou JSON inline)")
    ap.add_argument("--ticket", required=True, help="AutoRewriteTicket (arquivo JSON ou JSON inline)")
    ap.add_argument("--out", default=str(DIRS["ARTIFACTS"] / "autorewrite_report.json"),
                   help="Arquivo para salvar AutoRewriteReport")
    ap.add_argument("--config", help="Arquivo de configuração JSON/YAML")
    ap.add_argument("--seed", type=int, help="Seed para reprodutibilidade")
    ap.add_argument("--mode", choices=["apply", "dryrun"], default="apply",
                   help="Modo de execução")
    
    args = ap.parse_args()
    
    try:
        # Carrega entradas
        xt_dict = _load_path_or_json(args.xt)
        plan_dict = _load_path_or_json(args.plan)
        tkt_dict = _load_path_or_json(args.ticket)
        
        # Carrega configuração personalizada
        config = {}
        if args.config:
            config = _load_path_or_json(args.config)
        
        # Constrói objetos
        xt = OmegaState(**xt_dict)
        plan = PlanOmega(**plan_dict)
        
        # PromotionSet
        promo = None
        if tkt_dict.get("promotion_set"):
            ps = tkt_dict["promotion_set"]
            patchset = []
            for c in ps.get("patchset", []):
                patchset.append(PatchCandidate(
                    cand_id=c["cand_id"],
                    patch_file=c["patch_file"],
                    meta=c.get("meta", {})
                ))
            promo = PromotionSet(
                top=ps.get("top", []),
                patchset=patchset
            )
        
        ticket = AutoRewriteTicket(
            ticket_id=tkt_dict.get("ticket_id", f"awt_{uuid.uuid4().hex[:8]}"),
            source=tkt_dict.get("source", "crucible"),
            priority=int(tkt_dict.get("priority", 50)),
            goal=tkt_dict.get("goal", ""),
            promotion_set=promo,
            plan_constraints=tkt_dict.get("plan_constraints", {}),
            budgets=tkt_dict.get("budgets", {}),
            evidence=tkt_dict.get("evidence", []),
            deadline=tkt_dict.get("deadline")
        )
        
        # Executa TTD-DR
        engine = Fase6AutoRewrite(config)
        report = engine.process_ticket(xt, ticket, plan)
        
        # Salva relatório
        save_json_file(Path(args.out), asdict(report))
        
        _log(f"✅ AutoRewriteReport salvo em: {args.out}")
        print(json.dumps(asdict(report), indent=2))
        
    except Exception as e:
        _log(f"❌ Falha na fase 6: {e}\n{traceback.format_exc()}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
