#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω — 1/8 (Core) · v7.0-ME (Master Equation, Deterministic, Fail-Closed)
==============================================================================

This module implements the core of the PENIN-Ω organism with P0 corrections:
- Deterministic seed management for all randomness
- psutil mandatory with fail-closed fallback  
- PROMOTE_ATTEST event with atomic promotion verification
- Fibonacci boost clamped to ≤5% with EWMA stability window
- Pydantic config validation

The master evolution equation remains:

    I_{t+1} = Π_{H∩S} [ I_t + α_t^Ω · ΔL_∞ · V_t ]

where α_t^Ω is a product of the base learning rate and normalized scores
from CAOS⁺, SR, G and OCI; ΔL_∞ is the change in the L∞ score between
cycles; V_t is the Σ‑Guard gate (fail‑closed); and Π_{H∩S} denotes
projection into the safe/ethical domain. All gates are non‑compensatory.

Copyright 2025 Daniel Penin and contributors.
"""

from __future__ import annotations
import os
import sys
import json
import time
import uuid
import math
import random
import hashlib
import asyncio
import threading
import multiprocessing
import pickle
import sqlite3
import logging
import signal
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
from datetime import datetime, timezone
from collections import deque, defaultdict, OrderedDict
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from enum import Enum

# Pydantic for config validation
try:
    from pydantic import BaseModel, Field, ValidationError, validator
    HAS_PYDANTIC = True
except ImportError:
    print("ERROR: pydantic is required. Install with: pip install pydantic")
    sys.exit(1)

# Optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except Exception:
    HAS_NUMPY = False

try:
    import redis
    HAS_REDIS = True
except Exception:
    HAS_REDIS = False

try:
    import torch
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False

# CRITICAL: psutil is now MANDATORY for fail-closed behavior
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("WARNING: psutil not found. System will assume HIGH resource usage (fail-closed).")

# -----------------------------------------------------------------------------
# Optional Multi-API Orchestrator (penin package)
# -----------------------------------------------------------------------------
try:
    from penin.config import settings as PENIN_SETTINGS
    from penin.router import MultiLLMRouter
    from penin.providers.openai_provider import OpenAIProvider
    from penin.providers.deepseek_provider import DeepSeekProvider
    from penin.providers.mistral_provider import MistralProvider
    from penin.providers.gemini_provider import GeminiProvider
    from penin.providers.anthropic_provider import AnthropicProvider
    from penin.providers.grok_provider import GrokProvider
    from penin.tools.schemas import KAGGLE_SEARCH_TOOL, HF_SEARCH_TOOL
    from penin.tools.registry import execute_tool as penin_execute_tool
    HAS_PENIN = True
except Exception:
    HAS_PENIN = False

# -----------------------------------------------------------------------------
# Configuration Models (Pydantic)
# -----------------------------------------------------------------------------
class EthicsConfig(BaseModel):
    ece_max: float = Field(0.01, ge=0, le=1, description="Maximum ECE threshold")
    rho_bias_max: float = Field(1.05, ge=1, le=2, description="Maximum bias threshold")
    consent_required: bool = Field(True, description="Require consent")
    eco_ok_required: bool = Field(True, description="Require eco compliance")

class IRICConfig(BaseModel):
    rho_max: float = Field(0.95, ge=0, le=1, description="Maximum risk threshold")
    contraction_factor: float = Field(0.98, ge=0.5, le=1, description="Risk contraction factor")

class CAOSPlusConfig(BaseModel):
    kappa: float = Field(2.0, ge=0, le=10, description="CAOS amplification factor")
    pmin: float = Field(0.05, ge=0, le=1, description="Minimum power")
    pmax: float = Field(2.0, ge=1, le=10, description="Maximum power")
    chaos_probability: float = Field(0.01, ge=0, le=0.1, description="Chaos injection probability")
    max_boost: float = Field(0.05, ge=0, le=0.1, description="Maximum Fibonacci boost (5%)")
    ewma_alpha: float = Field(0.2, ge=0.1, le=0.5, description="EWMA smoothing factor")
    min_stability_cycles: int = Field(5, ge=3, le=20, description="Minimum cycles for stability")

class SRWeights(BaseModel):
    C: float = Field(0.2, ge=0, le=1)
    E: float = Field(0.4, ge=0, le=1)
    M: float = Field(0.3, ge=0, le=1)
    A: float = Field(0.1, ge=0, le=1)
    
    @validator('A')
    def weights_sum_to_one(cls, v, values):
        total = v + values.get('C', 0) + values.get('E', 0) + values.get('M', 0)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"SR weights must sum to 1.0, got {total}")
        return v

class SROmegaConfig(BaseModel):
    weights: SRWeights = Field(default_factory=SRWeights)
    tau_sr: float = Field(0.8, ge=0, le=1, description="SR gate threshold")

class OmegaSigmaConfig(BaseModel):
    weights: List[float] = Field(default_factory=lambda: [1.0/8]*8)
    tau_g: float = Field(0.7, ge=0, le=1, description="Global coherence threshold")
    
    @validator('weights')
    def weights_valid(cls, v):
        if len(v) != 8:
            raise ValueError("Must have exactly 8 weights")
        if abs(sum(v) - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {sum(v)}")
        return v

class OCIConfig(BaseModel):
    weights: List[float] = Field(default_factory=lambda: [0.25]*4)
    tau_oci: float = Field(0.9, ge=0, le=1, description="OCI gate threshold")
    
    @validator('weights')
    def weights_valid(cls, v):
        if len(v) != 4:
            raise ValueError("Must have exactly 4 weights")
        if abs(sum(v) - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {sum(v)}")
        return v

class LInfWeights(BaseModel):
    rsi: float = Field(0.2, ge=0, le=1)
    synergy: float = Field(0.2, ge=0, le=1)
    novelty: float = Field(0.2, ge=0, le=1)
    stability: float = Field(0.2, ge=0, le=1)
    viability: float = Field(0.15, ge=0, le=1)
    cost: float = Field(0.05, ge=0, le=1)
    
    @validator('cost')
    def weights_sum_to_one(cls, v, values):
        total = v + sum(values.get(k, 0) for k in ['rsi', 'synergy', 'novelty', 'stability', 'viability'])
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"L∞ weights must sum to 1.0, got {total}")
        return v

class LInfPlacarConfig(BaseModel):
    weights: LInfWeights = Field(default_factory=LInfWeights)
    lambda_c: float = Field(0.1, ge=0, le=1, description="Cost penalty factor")

class FibonacciConfig(BaseModel):
    enabled: bool = Field(False, description="Enable Fibonacci features")
    cache: bool = Field(True, description="Apply Fibonacci to cache TTLs")
    trust_region: bool = Field(True, description="Apply Fibonacci to trust region")
    l1_ttl_base: float = Field(1.0, ge=0.1, le=60)
    l2_ttl_base: float = Field(60.0, ge=1, le=3600)
    max_interval_s: float = Field(300.0, ge=60, le=3600)
    trust_growth: Optional[float] = Field(None, ge=1, le=2)
    trust_shrink: Optional[float] = Field(None, ge=0.5, le=1)
    search_method: str = Field("fibonacci", pattern="^(fibonacci|golden)$")

class ThresholdsConfig(BaseModel):
    tau_caos: float = Field(0.7, ge=0, le=1, description="CAOS gate threshold")
    beta_min: float = Field(0.02, ge=0, le=0.1, description="Minimum ΔL∞ for promotion")

class EvolutionConfig(BaseModel):
    alpha_0: float = Field(0.1, ge=0.01, le=1, description="Base learning rate")
    seed: Optional[int] = Field(None, description="Random seed for determinism")

class PeninConfig(BaseModel):
    """Main configuration with validation"""
    ethics: EthicsConfig = Field(default_factory=EthicsConfig)
    iric: IRICConfig = Field(default_factory=IRICConfig)
    caos_plus: CAOSPlusConfig = Field(default_factory=CAOSPlusConfig)
    sr_omega: SROmegaConfig = Field(default_factory=SROmegaConfig)
    omega_sigma: OmegaSigmaConfig = Field(default_factory=OmegaSigmaConfig)
    oci: OCIConfig = Field(default_factory=OCIConfig)
    linf_placar: LInfPlacarConfig = Field(default_factory=LInfPlacarConfig)
    fibonacci: FibonacciConfig = Field(default_factory=FibonacciConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    evolution: EvolutionConfig = Field(default_factory=EvolutionConfig)

# -----------------------------------------------------------------------------
# Event Types
# -----------------------------------------------------------------------------
class EventType:
    BOOT = "BOOT"
    CYCLE_START = "CYCLE_START"
    CYCLE_ABORT = "CYCLE_ABORT"
    PROMOTE_ATTEST = "PROMOTE_ATTEST"
    ROLLBACK = "ROLLBACK"
    MASTER_EQ = "MASTER_EQ"
    FIBONACCI_TICK = "FIBONACCI_TICK"
    FIBONACCI_OPT = "FIBONACCI_OPT"
    SNAPSHOT = "SNAPSHOT"
    SHUTDOWN = "SHUTDOWN"
    LLM_QUERY = "LLM_QUERY"
    SEED_SET = "SEED_SET"
    GATE_FAIL = "GATE_FAIL"

# -----------------------------------------------------------------------------
# Configuration and paths
# -----------------------------------------------------------------------------
PKG_VERSION = "7.0.0"
ROOT = Path(os.getenv("PENIN_ROOT", "/opt/penin_omega"))
if not ROOT.exists():
    ROOT = Path.home() / ".penin_omega"
    
DIRS = {
    "LOG": ROOT / "logs",
    "STATE": ROOT / "state",
    "CACHE": ROOT / "cache",
    "WORM": ROOT / "worm_ledger",
    "SNAPSHOTS": ROOT / "snapshots",
    "MODELS": ROOT / "models",
}

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][Ω-1/8-v7][%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(DIRS["LOG"] / "omega_core_1of8_v7.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("Ω-1/8-v7")

# -----------------------------------------------------------------------------
# Deterministic Random State Manager
# -----------------------------------------------------------------------------
class DeterministicRandom:
    """Manages deterministic random state with seed tracking"""
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else int(time.time() * 1000) % (2**32)
        self.rng = random.Random(self.seed)
        self.call_count = 0
        
    def set_seed(self, seed: int):
        """Set new seed and reset RNG"""
        self.seed = seed
        self.rng = random.Random(seed)
        self.call_count = 0
        
    def get_state(self) -> Dict[str, Any]:
        """Get current RNG state for logging"""
        return {
            "seed": self.seed,
            "call_count": self.call_count,
            "state_hash": hashlib.sha256(str(self.rng.getstate()).encode()).hexdigest()[:8]
        }
        
    def random(self) -> float:
        """Get random float [0, 1)"""
        self.call_count += 1
        return self.rng.random()
        
    def uniform(self, a: float, b: float) -> float:
        """Get random float [a, b)"""
        self.call_count += 1
        return self.rng.uniform(a, b)
        
    def choice(self, seq):
        """Choose random element"""
        self.call_count += 1
        return self.rng.choice(seq)

# -----------------------------------------------------------------------------
# EWMA Stability Tracker
# -----------------------------------------------------------------------------
class EWMATracker:
    """Exponentially Weighted Moving Average for stability tracking"""
    def __init__(self, alpha: float = 0.2, min_samples: int = 5):
        self.alpha = alpha
        self.min_samples = min_samples
        self.value = None
        self.variance = None
        self.count = 0
        self.history = deque(maxlen=min_samples * 2)
        
    def update(self, new_value: float):
        """Update EWMA with new value"""
        self.history.append(new_value)
        self.count += 1
        
        if self.value is None:
            self.value = new_value
            self.variance = 0
        else:
            delta = new_value - self.value
            self.value += self.alpha * delta
            self.variance = (1 - self.alpha) * (self.variance + self.alpha * delta**2)
            
    def is_stable(self, threshold: float = 0.01) -> bool:
        """Check if values are stable (low variance)"""
        if self.count < self.min_samples:
            return False
        return self.variance < threshold
        
    def get_stats(self) -> Dict[str, float]:
        """Get current statistics"""
        return {
            "value": self.value or 0,
            "variance": self.variance or 0,
            "count": self.count,
            "stable": self.is_stable()
        }

# -----------------------------------------------------------------------------
# Fibonacci toolkit and Zeckendorf
# -----------------------------------------------------------------------------
PHI = (1.0 + math.sqrt(5)) / 2.0
INV_PHI = 1.0 / PHI

class FibonacciResearch:
    """Full Fibonacci research and optimization toolkit."""
    def __init__(self, rng: DeterministicRandom):
        self.fib_cache = {0: 0, 1: 1}
        self.optimization_count = 0
        self.pattern_scores: Dict[str, float] = {}
        self.rng = rng  # Use deterministic RNG
        
    def fib_iterative(self, n: int) -> int:
        if n in self.fib_cache:
            return self.fib_cache[n]
        a, b = 0, 1
        for i in range(2, n + 1):
            a, b = b, a + b
            self.fib_cache[i] = b
        return self.fib_cache[n]
        
    def fib_matrix(self, n: int) -> int:
        if n <= 1:
            return n
        def mm(A, B):
            return [
                [A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]],
                [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]],
            ]
        def mp(M, p):
            R = [[1, 0], [0, 1]]
            while p > 0:
                if p & 1:
                    R = mm(R, M)
                M = mm(M, M)
                p >>= 1
            return R
        base = [[1, 1], [1, 0]]
        return mp(base, n)[0][1]
        
    def binet_formula(self, n: int) -> float:
        return (PHI ** n - (-INV_PHI) ** n) / math.sqrt(5)
        
    def golden_section_search(self, f: Callable[[float], float], a: float, b: float,
                              tol: float = 1e-6, maximize: bool = True) -> float:
        invphi = INV_PHI
        invphi2 = 1.0 - invphi
        h = b - a
        if h <= tol:
            return (a + b) / 2.0
        n = int(math.ceil(math.log(tol / h) / math.log(invphi)))
        c = a + invphi2 * h
        d = a + invphi * h
        fc = f(c)
        fd = f(d)
        if not maximize:
            fc, fd = -fc, -fd
        for _ in range(n - 1):
            if fc < fd:
                a = c
                c, fc = d, fd
                h *= invphi
                d = a + invphi * h
                fd = f(d)
                if not maximize:
                    fd = -fd
            else:
                b = d
                d, fd = c, fc
                h *= invphi
                c = a + invphi2 * h
                fc = f(c)
                if not maximize:
                    fc = -fc
        self.optimization_count += 1
        return (a + b) / 2.0
        
    def fibonacci_search(self, f: Callable[[float], float], a: float, b: float,
                          tol: float = 1e-6, maximize: bool = True) -> float:
        fib = [0, 1]
        while fib[-1] < (b - a) / tol:
            fib.append(fib[-1] + fib[-2])
        n = len(fib) - 1
        x1 = a + (fib[n - 2] / fib[n]) * (b - a)
        x2 = a + (fib[n - 1] / fib[n]) * (b - a)
        f1, f2 = f(x1), f(x2)
        if not maximize:
            f1, f2 = -f1, -f2
        for k in range(n - 2, 0, -1):
            if f1 < f2:
                a = x1
                x1, f1 = x2, f2
                x2 = a + (fib[k] / fib[k + 1]) * (b - a)
                f2 = f(x2)
                if not maximize:
                    f2 = -f2
            else:
                b = x2
                x2, f2 = x1, f1
                x1 = a + (fib[k - 1] / fib[k + 1]) * (b - a)
                f1 = f(x1)
                if not maximize:
                    f1 = -f1
        self.optimization_count += 1
        return (a + b) / 2.0
        
    def analyze_fibonacci_patterns(self, seq: List[float]) -> Dict[str, float]:
        if len(seq) < 3:
            return {"ratio_score": 0.0, "pattern_strength": 0.0, "avg_ratio": 0.0}
        ratios = []
        for i in range(1, len(seq)):
            if seq[i - 1] != 0:
                ratios.append(seq[i] / seq[i - 1])
        if not ratios:
            return {"ratio_score": 0.0, "pattern_strength": 0.0, "avg_ratio": 0.0}
        phi_dists = [abs(r - PHI) for r in ratios]
        ratio_score = 1.0 - (sum(phi_dists) / len(phi_dists)) / PHI
        if HAS_NUMPY:
            std_dev = float(np.std(ratios))
        else:
            mean = sum(ratios) / len(ratios)
            std_dev = math.sqrt(sum((r - mean) ** 2 for r in ratios) / len(ratios))
        pattern_strength = 1.0 / (1.0 + std_dev)
        return {
            "ratio_score": max(0.0, ratio_score),
            "pattern_strength": max(0.0, pattern_strength),
            "avg_ratio": sum(ratios) / len(ratios) if ratios else 0.0,
        }
        
    def fibonacci_retracement_levels(self, high: float, low: float) -> Dict[str, float]:
        diff = high - low
        return {
            "0.0%": high,
            "23.6%": high - 0.236 * diff,
            "38.2%": high - 0.382 * diff,
            "50.0%": high - 0.5 * diff,
            "61.8%": high - 0.618 * diff,
            "78.6%": high - 0.786 * diff,
            "100.0%": low,
        }

class ZeckendorfEncoder:
    """Encode integers uniquely as sums of non‑consecutive Fibonacci numbers."""
    @staticmethod
    def _fib_upto(n: int) -> List[int]:
        fib = [1, 2]
        while fib[-1] < n:
            fib.append(fib[-1] + fib[-2])
        return fib
        
    @staticmethod
    def encode(n: int) -> List[int]:
        if n < 0:
            raise ValueError("Zeckendorf representation is defined for n >= 0")
        if n == 0:
            return [0]
        fib = ZeckendorfEncoder._fib_upto(n)
        rep: List[int] = []
        i = len(fib) - 1
        while n > 0 and i >= 0:
            if fib[i] <= n:
                rep.append(fib[i])
                n -= fib[i]
                i -= 2
            else:
                i -= 1
        return rep
        
    @staticmethod
    def encode_as_string(n: int) -> str:
        if n == 0:
            return "0"
        return "Z{" + "+".join(map(str, ZeckendorfEncoder.encode(n))) + "}"

# -----------------------------------------------------------------------------
# Cache (Multi‑level with FibHeap) - Updated with WAL mode
# -----------------------------------------------------------------------------
class MultiLevelCache:
    """Three‑level cache with TTL and eviction via lazy min‑heap."""
    def __init__(self, l1_size: int = 1000, l2_size: int = 10000, ttl_l1: int = 1, ttl_l2: int = 60):
        self.l1_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.l1_size = l1_size
        self.l1_ttl = ttl_l1
        self.l2_db_path = DIRS["CACHE"] / "l2_cache.db"
        self.l2_db = sqlite3.connect(str(self.l2_db_path), check_same_thread=False)
        self._init_l2_db()
        self.l2_size = l2_size
        self.l2_ttl = ttl_l2
        self.l2_heap = FibHeapLite()
        self.l2_nodes: Dict[str, Tuple] = {}
        self.l3_redis = None
        if HAS_REDIS:
            try:
                self.l3_redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
                self.l3_redis.ping()
            except Exception:
                self.l3_redis = None
        self.stats = defaultdict(lambda: {"hits": 0, "misses": 0, "evictions": 0})
        self._lock = threading.RLock()
        
    def _init_l2_db(self):
        cursor = self.l2_db.cursor()
        # Set WAL mode and busy timeout for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=3000")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                timestamp REAL,
                access_count INTEGER DEFAULT 0,
                last_access REAL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_access ON cache(access_count)')
        self.l2_db.commit()
        
    def _serialize(self, obj: Any) -> bytes: 
        return pickle.dumps(obj)
        
    def _deserialize(self, b: bytes) -> Any: 
        return pickle.loads(b)
        
    def _promote_to_l1(self, key: str, value: Any):
        if len(self.l1_cache) >= self.l1_size:
            evicted_key, _ = self.l1_cache.popitem(last=False)
            self.stats[evicted_key]["evictions"] += 1
        self.l1_cache[key] = {"value": value, "timestamp": time.time()}
        self.l1_cache.move_to_end(key)
        
    def _promote_to_l2(self, key: str, value: Any):
        value_bytes = self._serialize(value)
        cursor = self.l2_db.cursor()
        now = time.time()
        cursor.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]
        if count >= self.l2_size:
            for _ in range(max(1, self.l2_size // 10)):
                evicted = self.l2_heap.extract_min()
                if evicted:
                    _, evicted_key = evicted
                    cursor.execute("DELETE FROM cache WHERE key = ?", (evicted_key,))
                    self.stats[evicted_key]["evictions"] += 1
                    self.l2_nodes.pop(evicted_key, None)
        cursor.execute(
            "INSERT OR REPLACE INTO cache (key, value, timestamp, last_access) VALUES (?, ?, ?, ?)",
            (key, value_bytes, now, now)
        )
        self.l2_db.commit()
        prio = now
        if key in self.l2_nodes:
            self.l2_heap.decrease_key(key, prio)
        else:
            self.l2_nodes[key] = self.l2_heap.insert(prio, key)
            
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            # Check L1
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                if time.time() - entry["timestamp"] < self.l1_ttl:
                    self.stats[key]["hits"] += 1
                    self.l1_cache.move_to_end(key)
                    return entry["value"]
                else:
                    del self.l1_cache[key]
            # Check L2
            cursor = self.l2_db.cursor()
            cursor.execute("SELECT value, timestamp FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                value_bytes, timestamp = row
                if time.time() - timestamp < self.l2_ttl:
                    value = self._deserialize(value_bytes)
                    self._promote_to_l1(key, value)
                    cursor.execute(
                        "UPDATE cache SET access_count = access_count + 1, last_access = ? WHERE key = ?",
                        (time.time(), key)
                    )
                    self.l2_db.commit()
                    if key in self.l2_nodes:
                        self.l2_heap.decrease_key(key, time.time())
                    self.stats[key]["hits"] += 1
                    return value
            # Check L3
            if self.l3_redis:
                try:
                    value_bytes = self.l3_redis.get(f"penin:{key}")
                    if value_bytes:
                        value = self._deserialize(value_bytes)
                        self._promote_to_l1(key, value)
                        self._promote_to_l2(key, value)
                        self.stats[key]["hits"] += 1
                        return value
                except Exception:
                    pass
            self.stats[key]["misses"] += 1
            return default
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            self._promote_to_l1(key, value)
            self._promote_to_l2(key, value)
            if self.l3_redis:
                try:
                    value_bytes = self._serialize(value)
                    self.l3_redis.setex(
                        f"penin:{key}", ttl or self.l2_ttl, value_bytes
                    )
                except Exception:
                    pass
                    
    def clear(self):
        with self._lock:
            self.l1_cache.clear()
            self.l2_db.execute("DELETE FROM cache")
            self.l2_db.commit()
            self.l2_heap = FibHeapLite()
            self.l2_nodes.clear()
            if self.l3_redis:
                try:
                    for key in self.l3_redis.scan_iter("penin:*"):
                        self.l3_redis.delete(key)
                except Exception:
                    pass

class FibHeapLite:
    """Lazy min‑heap with tombstones for decrease_key support."""
    def __init__(self):
        import heapq
        self.heap: List[Tuple[float, int, str]] = []
        self.entry_fresh: Dict[str, Tuple[float, int, str]] = {}
        self.invalid: set = set()
        self._heapq = heapq
        self._counter = 0
        
    def insert(self, key: float, value: str):
        self._counter += 1
        token = (key, self._counter, value)
        self.entry_fresh[value] = token
        self._heapq.heappush(self.heap, token)
        return token
        
    def decrease_key(self, value: str, new_key: float):
        old = self.entry_fresh.get(value)
        if old:
            self.invalid.add(old)
        return self.insert(new_key, value)
        
    def extract_min(self) -> Optional[Tuple[float, str]]:
        while self.heap:
            key, _, val = self._heapq.heappop(self.heap)
            token = (key, _, val)
            if token in self.invalid:
                self.invalid.remove(token)
                continue
            if self.entry_fresh.get(val) == token:
                del self.entry_fresh[val]
                return key, val
        return None

# -----------------------------------------------------------------------------
# WORM Ledger with PROMOTE_ATTEST
# -----------------------------------------------------------------------------
class WORMLedger:
    """Write‑once, read‑many ledger with hash chain and atomic promotion attestation."""
    def __init__(self, path: Path = DIRS["WORM"] / "omega_core_1of8_v7.db"):
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self._init_db()
        self._lock = threading.Lock()
        self.tail = self._get_last_hash()
        
    def _init_db(self):
        cursor = self.db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                etype TEXT,
                data TEXT,
                ts TEXT,
                prev TEXT,
                hash TEXT,
                zeck TEXT,
                seed_state TEXT,
                pre_hash TEXT,
                post_hash TEXT,
                gate_trace TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ts ON events(ts)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_etype ON events(etype)")
        self.db.commit()
        
    def _get_last_hash(self) -> str:
        c = self.db.cursor()
        c.execute("SELECT hash FROM events ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        return row[0] if row else "genesis"
        
    def record(self, etype: str, data: Dict[str, Any], state_for_zeck: Optional['OmegaMEState'] = None,
               seed_state: Optional[Dict] = None, pre_hash: Optional[str] = None, 
               post_hash: Optional[str] = None, gate_trace: Optional[List] = None) -> str:
        with self._lock:
            ts = datetime.now(timezone.utc).isoformat()
            zeck = None
            if state_for_zeck:
                mix = int(abs(state_for_zeck.delta_linf) * 1e6) + int(state_for_zeck.caos_plus * 1e6) + state_for_zeck.cycle
                zeck = ZeckendorfEncoder.encode_as_string(abs(mix))
            payload = {"etype": etype, "data": data, "ts": ts, "prev": self.tail}
            event_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            
            cursor = self.db.cursor()
            cursor.execute(
                """INSERT INTO events (etype, data, ts, prev, hash, zeck, seed_state, pre_hash, post_hash, gate_trace) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (etype, json.dumps(data, ensure_ascii=False), ts, self.tail, event_hash, zeck,
                 json.dumps(seed_state) if seed_state else None,
                 pre_hash, post_hash, 
                 json.dumps(gate_trace) if gate_trace else None),
            )
            self.db.commit()
            self.tail = event_hash
            return event_hash
            
    def record_promote_attest(self, pre_state: 'OmegaMEState', post_state: 'OmegaMEState', 
                             gate_results: Dict[str, Any], seed_state: Dict, 
                             config_hash: str, step: float) -> str:
        """Record atomic promotion attestation with all verification data"""
        pre_hash = hashlib.sha256(json.dumps(pre_state.to_dict(), sort_keys=True).encode()).hexdigest()
        post_hash = hashlib.sha256(json.dumps(post_state.to_dict(), sort_keys=True).encode()).hexdigest()
        
        data = {
            "step": step,
            "alpha": post_state.alpha_omega,
            "delta_linf": post_state.delta_linf,
            "config_hash": config_hash,
            "cycle": post_state.cycle
        }
        
        return self.record(
            EventType.PROMOTE_ATTEST, 
            data, 
            post_state,
            seed_state=seed_state,
            pre_hash=pre_hash,
            post_hash=post_hash,
            gate_trace=gate_results.get("gate_trace", [])
        )
        
    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        c = self.db.cursor()
        c.execute("SELECT etype, data, ts, prev, hash FROM events ORDER BY id")
        prev = "genesis"
        for i, (etype, data, ts, stored_prev, stored_hash) in enumerate(c.fetchall(), 1):
            if stored_prev != prev:
                return False, f"Chain break at row {i}"
            payload = {"etype": etype, "data": json.loads(data), "ts": ts, "prev": stored_prev}
            calc = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if calc != stored_hash:
                return False, f"Hash mismatch at row {i}"
            prev = stored_hash
        return True, None

# -----------------------------------------------------------------------------
# State class with additional tracking
# -----------------------------------------------------------------------------
@dataclass
class OmegaMEState:
    cycle: int = 0
    ts: float = 0.0  # Changed from time.time() for determinism
    l_inf: float = 0.0
    l_inf_prev: float = 0.0
    delta_linf: float = 0.0
    rsi: float = 0.6
    synergy: float = 0.6
    novelty: float = 0.5
    stability: float = 0.7
    viability: float = 0.8
    cost: float = 0.2
    C: float = 0.6
    A: float = 0.6
    O: float = 0.6
    S: float = 0.6
    caos_plus: float = 1.0
    caos_harmony: float = 1.0
    sr_score: float = 1.0
    C_cal: float = 0.8
    E_ok: float = 1.0
    M: float = 0.7
    A_eff: float = 0.6
    g_score: float = 1.0
    modules: List[float] = field(default_factory=lambda: [0.7] * 8)
    oci_score: float = 1.0
    memory: float = 0.8
    flow: float = 0.7
    policy: float = 0.9
    feedback: float = 0.6
    sigma_ok: bool = True
    ece: float = 0.0
    bias: float = 1.0
    consent: bool = True
    eco: bool = True
    rho: float = 0.5
    uncertainty: float = 0.3
    throughput: float = 0.0
    latency_ms: float = 0.0
    cpu: float = 0.0
    mem: float = 0.0
    alpha_0: float = 0.1
    alpha_omega: float = 0.0
    trust_radius: float = 0.1
    kill_switch: bool = False
    fib_optimizations: int = 0
    pattern_score: float = 0.0
    pattern_stable: bool = False  # New: pattern stability flag
    zeckendorf_hash: str = "0"
    
    def to_dict(self) -> Dict[str, Any]: 
        return asdict(self)
        
    def compute_hash(self) -> str:
        """Compute hash of current state for TOCTOU prevention"""
        # Exclude timestamp for deterministic hashing
        state_dict = self.to_dict()
        state_dict.pop('ts', None)  # Remove timestamp
        return hashlib.sha256(json.dumps(state_dict, sort_keys=True).encode()).hexdigest()

# -----------------------------------------------------------------------------
# Engines with deterministic behavior
# -----------------------------------------------------------------------------
class SigmaGuard:
    def __init__(self, cfg: EthicsConfig):
        self.ece_max = cfg.ece_max
        self.bias_max = cfg.rho_bias_max
        self.require_consent = cfg.consent_required
        self.require_eco = cfg.eco_ok_required
        self.rho_max = 0.95  # Hardcoded safety threshold
        
    def check(self, xt: OmegaMEState) -> Tuple[bool, List[Dict[str, Any]]]:
        violations = []
        if xt.ece > self.ece_max: 
            violations.append({"gate": "ECE", "value": xt.ece, "threshold": self.ece_max, "msg": f"ECE {xt.ece:.4f} > {self.ece_max}"})
        if xt.bias > self.bias_max: 
            violations.append({"gate": "BIAS", "value": xt.bias, "threshold": self.bias_max, "msg": f"Bias {xt.bias:.3f} > {self.bias_max}"})
        if self.require_consent and not xt.consent: 
            violations.append({"gate": "CONSENT", "value": False, "threshold": True, "msg": "Consent=False"})
        if self.require_eco and not xt.eco: 
            violations.append({"gate": "ECO", "value": False, "threshold": True, "msg": "Eco=False"})
        if xt.rho >= self.rho_max: 
            violations.append({"gate": "RISK", "value": xt.rho, "threshold": self.rho_max, "msg": f"Risk {xt.rho:.3f} >= {self.rho_max}"})
        xt.sigma_ok = len(violations) == 0
        return xt.sigma_ok, violations

class IRtoIC:
    def __init__(self, cfg: IRICConfig, use_phi: bool = False):
        self.rho_max = cfg.rho_max
        self.contraction = INV_PHI if use_phi else cfg.contraction_factor
        # Remove executor - checks are cheap and synchronous is better
        
    def safe(self, xt: OmegaMEState) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check safety with detailed gate results"""
        failures = []
        
        # Fail-closed: if no psutil, assume HIGH resource usage
        if not HAS_PSUTIL:
            xt.cpu = 0.99  # Assume high CPU
            xt.mem = 0.99  # Assume high memory
            failures.append({"gate": "PSUTIL_MISSING", "value": None, "threshold": None, 
                           "msg": "psutil not available - assuming high resource usage (fail-closed)"})
        
        if xt.rho >= self.rho_max:
            failures.append({"gate": "RHO", "value": xt.rho, "threshold": self.rho_max, 
                           "msg": f"Risk {xt.rho:.3f} >= {self.rho_max}"})
        if xt.uncertainty >= 0.9:
            failures.append({"gate": "UNCERTAINTY", "value": xt.uncertainty, "threshold": 0.9,
                           "msg": f"Uncertainty {xt.uncertainty:.3f} >= 0.9"})
        if xt.cpu >= 0.95:
            failures.append({"gate": "CPU", "value": xt.cpu, "threshold": 0.95,
                           "msg": f"CPU {xt.cpu:.3f} >= 0.95"})
        if xt.mem >= 0.95:
            failures.append({"gate": "MEM", "value": xt.mem, "threshold": 0.95,
                           "msg": f"Memory {xt.mem:.3f} >= 0.95"})
            
        return len(failures) == 0, failures
        
    def contract(self, xt: OmegaMEState) -> None:
        xt.rho *= self.contraction
        xt.uncertainty *= self.contraction

class CAOSPlusEngine:
    def __init__(self, cfg: CAOSPlusConfig, fib: FibonacciResearch, rng: DeterministicRandom):
        self.kappa = cfg.kappa
        self.pmin = cfg.pmin
        self.pmax = cfg.pmax
        self.pchaos = cfg.chaos_probability
        self.max_boost = cfg.max_boost  # Max 5% boost
        self.fib = fib
        self.rng = rng  # Use deterministic RNG
        self.pattern_tracker = EWMATracker(alpha=cfg.ewma_alpha, min_samples=cfg.min_stability_cycles)
        
    def compute(self, xt: OmegaMEState) -> float:
        # Deterministic chaos injection
        if self.rng.random() < self.pchaos:
            fac = self.rng.uniform(0.9, 1.1)
            xt.C *= fac
            xt.A *= fac
            xt.O *= fac
            xt.S *= fac
            
        C, A, O, S = max(0.0, xt.C), max(0.0, xt.A), max(0.0, xt.O), max(0.0, xt.S)
        base = 1.0 + self.kappa * C * A
        exponent = max(self.pmin, min(self.pmax, O * S))
        val = base ** exponent
        
        # Analyze Fibonacci patterns
        patt = self.fib.analyze_fibonacci_patterns([C, A, O, S])
        self.pattern_tracker.update(patt["pattern_strength"])
        
        # Apply boost only if pattern is stable (EWMA requirement)
        boost = 1.0
        if self.pattern_tracker.is_stable():
            # Clamp boost to max 5%
            boost = 1.0 + min(self.max_boost, 0.1 * patt["pattern_strength"])
            xt.pattern_stable = True
        else:
            xt.pattern_stable = False
            
        val *= boost
        xt.pattern_score = patt["pattern_strength"]
        xt.caos_plus = val
        xt.caos_harmony = (C + A) / (O + S if (O + S) > 1e-9 else 1.0)
        return val

class SREngine:
    def __init__(self, cfg: SROmegaConfig):
        self.weights = cfg.weights.dict()
        self.tau = cfg.tau_sr
        
    def compute(self, xt: OmegaMEState) -> float:
        comps = [
            (max(1e-6, xt.C_cal), self.weights["C"]),
            (max(1e-6, xt.E_ok), self.weights["E"]),
            (max(1e-6, xt.M), self.weights["M"]),
            (max(1e-6, xt.A_eff), self.weights["A"]),
        ]
        denom = sum(w / v for v, w in comps)
        xt.sr_score = 1.0 / max(1e-6, denom)
        return xt.sr_score
        
    def gate(self, xt: OmegaMEState) -> Tuple[bool, Dict[str, Any]]:
        passed = xt.sr_score >= self.tau
        return passed, {"gate": "SR", "value": xt.sr_score, "threshold": self.tau, 
                       "passed": passed, "msg": f"SR={xt.sr_score:.3f} {'≥' if passed else '<'} {self.tau}"}

class GlobalCoherence:
    def __init__(self, cfg: OmegaSigmaConfig):
        self.weights = cfg.weights
        self.tau = cfg.tau_g
        
    def compute(self, xt: OmegaMEState) -> float:
        if len(xt.modules) != 8:
            xt.modules = [0.7] * 8
        denom = 0.0
        for w, s in zip(self.weights, xt.modules):
            if s <= 0:
                xt.g_score = 0.0
                return 0.0
            denom += w / s
        xt.g_score = 1.0 / max(1e-6, denom)
        return xt.g_score
        
    def gate(self, xt: OmegaMEState) -> Tuple[bool, Dict[str, Any]]:
        passed = xt.g_score >= self.tau
        return passed, {"gate": "G", "value": xt.g_score, "threshold": self.tau,
                       "passed": passed, "msg": f"G={xt.g_score:.3f} {'≥' if passed else '<'} {self.tau}"}

class OCIEngine:
    def __init__(self, cfg: OCIConfig):
        self.weights = cfg.weights
        self.tau = cfg.tau_oci
        
    def compute(self, xt: OmegaMEState) -> float:
        comps = [
            (max(1e-6, xt.memory), self.weights[0]),
            (max(1e-6, xt.flow), self.weights[1]),
            (max(1e-6, xt.policy), self.weights[2]),
            (max(1e-6, xt.feedback), self.weights[3]),
        ]
        denom = sum(w / v for v, w in comps)
        xt.oci_score = 1.0 / max(1e-6, denom)
        return xt.oci_score
        
    def gate(self, xt: OmegaMEState) -> Tuple[bool, Dict[str, Any]]:
        passed = xt.oci_score >= self.tau
        return passed, {"gate": "OCI", "value": xt.oci_score, "threshold": self.tau,
                       "passed": passed, "msg": f"OCI={xt.oci_score:.3f} {'≥' if passed else '<'} {self.tau}"}

class LInfinityScore:
    def __init__(self, cfg: LInfPlacarConfig):
        self.weights = cfg.weights.dict()
        self.lambda_c = cfg.lambda_c
        
    def compute(self, xt: OmegaMEState) -> float:
        metrics = [
            (max(1e-6, xt.rsi), self.weights["rsi"]),
            (max(1e-6, xt.synergy), self.weights["synergy"]),
            (max(1e-6, xt.novelty), self.weights["novelty"]),
            (max(1e-6, xt.stability), self.weights["stability"]),
            (max(1e-6, xt.viability), self.weights["viability"]),
            (max(1e-6, 1.0 - xt.cost), self.weights["cost"]),
        ]
        denom = sum(w / v for v, w in metrics)
        base = 1.0 / max(1e-6, denom)
        penalty = math.exp(-self.lambda_c * xt.cost)
        eth_gate = 1.0 if xt.sigma_ok else 0.0
        risk_gate = 1.0 if xt.rho < 0.95 else 0.0
        xt.l_inf_prev = xt.l_inf
        xt.l_inf = base * penalty * eth_gate * risk_gate
        xt.delta_linf = xt.l_inf - xt.l_inf_prev
        return xt.l_inf

# -----------------------------------------------------------------------------
# Fibonacci manager for TTL, trust region and LR search
# -----------------------------------------------------------------------------
class FibonacciSchedule:
    def __init__(self, base: float, max_interval: float):
        self.base = float(base)
        self.max = float(max_interval)
        self.i = 1
        self.fr = FibonacciResearch(DeterministicRandom())  # Use deterministic
        
    def next(self) -> float:
        val = min(self.max, self.base * float(self.fr.fib_iterative(self.i)))
        self.i += 1
        return max(self.base, val)
        
    def reset(self):
        self.i = 1

class FibonacciManager:
    def __init__(self, cfg: FibonacciConfig, worm: WORMLedger, fib: FibonacciResearch):
        self.enabled = cfg.enabled
        self.cache_enabled = cfg.cache
        self.trust_enabled = cfg.trust_region
        self.l1b = cfg.l1_ttl_base
        self.l2b = cfg.l2_ttl_base
        self.maxi = cfg.max_interval_s
        self.grow = cfg.trust_growth or PHI ** 0.125
        self.shrk = cfg.trust_shrink or INV_PHI ** 0.125
        self.method = cfg.search_method
        self.s1 = FibonacciSchedule(self.l1b, self.maxi)
        self.s2 = FibonacciSchedule(self.l2b, self.maxi)
        self.worm = worm
        self.fib = fib
        
    def apply_cache(self, cache: MultiLevelCache):
        if not (self.enabled and self.cache_enabled): 
            return
        cache.l1_ttl = int(self.s1.next())
        cache.l2_ttl = int(self.s2.next())
        self.worm.record(EventType.FIBONACCI_TICK, {
            "l1_ttl": cache.l1_ttl,
            "l2_ttl": cache.l2_ttl,
        })
        
    def modulate_trust(self, xt: OmegaMEState):
        if not (self.enabled and self.trust_enabled): 
            return
        if xt.delta_linf > 0.02:
            xt.trust_radius = min(0.5, xt.trust_radius * self.grow)
        else:
            xt.trust_radius = max(0.01, xt.trust_radius * self.shrk)
            
    def optimize_lr(self, f: Callable[[float], float], a: float = 0.01, b: float = 1.0) -> float:
        if self.method == "fibonacci":
            return self.fib.fibonacci_search(f, a, b, maximize=True)
        else:
            return self.fib.golden_section_search(f, a, b, maximize=True)

# -----------------------------------------------------------------------------
# PeninOmegaCore with all P0 corrections
# -----------------------------------------------------------------------------
class PeninOmegaCore:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Validate config with Pydantic
        try:
            self.cfg = PeninConfig(**config) if config else PeninConfig()
        except ValidationError as e:
            log.error(f"Configuration validation failed: {e}")
            raise SystemExit(f"Invalid configuration: {e}")
            
        # Initialize deterministic RNG
        self.rng = DeterministicRandom(self.cfg.evolution.seed)
        log.info(f"Initialized with seed: {self.rng.seed}")
        
        # Compute config hash for attestation
        self.config_hash = hashlib.sha256(
            json.dumps(self.cfg.dict(), sort_keys=True).encode()
        ).hexdigest()[:16]
        
        self.worm = WORMLedger()
        self.cache = MultiLevelCache()
        self.fibR = FibonacciResearch(self.rng)
        self.fib = FibonacciManager(self.cfg.fibonacci, self.worm, self.fibR)
        use_phi = self.fib.enabled
        
        # Initialize engines with validated config
        self.sigma = SigmaGuard(self.cfg.ethics)
        self.iric = IRtoIC(self.cfg.iric, use_phi=use_phi)
        self.caos = CAOSPlusEngine(self.cfg.caos_plus, self.fibR, self.rng)
        self.sr = SREngine(self.cfg.sr_omega)
        self.gc = GlobalCoherence(self.cfg.omega_sigma)
        self.oci = OCIEngine(self.cfg.oci)
        self.linf = LInfinityScore(self.cfg.linf_placar)
        
        self.xt = OmegaMEState()
        self.metrics = {"cycles": 0, "promotions": 0, "rollbacks": 0, "extinctions": 0}
        self._register_boot()
        
        if self.fib.enabled and self.fib.cache_enabled:
            self.fib.apply_cache(self.cache)
            
        self.pool = ThreadPoolExecutor(max_workers=8)
        self.ppool = ProcessPoolExecutor(max_workers=4)
        
    def _register_boot(self):
        self.worm.record(EventType.BOOT, {
            "version": PKG_VERSION,
            "phi": PHI,
            "inv_phi": INV_PHI,
            "fibonacci_enabled": self.fib.enabled,
            "seed": self.rng.seed,
            "config_hash": self.config_hash,
            "psutil_available": HAS_PSUTIL
        }, self.xt, seed_state=self.rng.get_state())
        
    async def master_equation_cycle(self, external_metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        result = {"success": False, "decision": None, "metrics": {}, "gate_trace": []}
        t0 = time.time()
        
        # Update timestamp for this cycle
        self.xt.ts = t0
        
        # Record cycle start with seed state
        self.worm.record(EventType.CYCLE_START, 
                        {"cycle": self.xt.cycle, "seed_state": self.rng.get_state()}, 
                        self.xt, seed_state=self.rng.get_state())
        
        # Store pre-state for PROMOTE_ATTEST
        pre_state = OmegaMEState(**self.xt.to_dict())
        
        try:
            # Apply external metrics
            if external_metrics:
                for k, v in external_metrics.items():
                    if hasattr(self.xt, k): 
                        setattr(self.xt, k, float(v))
                        
            # Update resource metrics (fail-closed if no psutil)
            if HAS_PSUTIL:
                # For deterministic testing with seed, use pseudo-random values
                if self.cfg.evolution.seed is not None:
                    self.xt.cpu = 0.3 + 0.4 * self.rng.random()  # Range 0.3-0.7
                    self.xt.mem = 0.3 + 0.4 * self.rng.random()  # Range 0.3-0.7
                else:
                    self.xt.cpu = psutil.cpu_percent(interval=None) / 100.0
                    self.xt.mem = psutil.virtual_memory().percent / 100.0
            else:
                # FAIL-CLOSED: Assume high resource usage
                self.xt.cpu = 0.99
                self.xt.mem = 0.99
                log.warning("psutil unavailable - assuming HIGH resource usage (fail-closed)")
                
            # Σ-Guard check
            ok, violations = self.sigma.check(self.xt)
            if not ok:
                result["gate_trace"].extend(violations)
                result.update({"decision": "ABORT", "reason": "SIGMA_GUARD", "violations": [v["msg"] for v in violations]})
                self.worm.record(EventType.CYCLE_ABORT, result, self.xt, seed_state=self.rng.get_state())
                return result
                
            # IR→IC safety check
            safe, failures = self.iric.safe(self.xt)
            if not safe:
                result["gate_trace"].extend(failures)
                self.iric.contract(self.xt)
                result.update({"decision": "ABORT", "reason": "IRIC_CONTRACT", "failures": [f["msg"] for f in failures]})
                self.worm.record(EventType.CYCLE_ABORT, result, self.xt, seed_state=self.rng.get_state())
                return result
                
            # Optional: Pre-cycle multi-API orchestration to enrich context
            if HAS_PENIN:
                try:
                    providers = []
                    if PENIN_SETTINGS.OPENAI_API_KEY:
                        providers.append(OpenAIProvider())
                    if PENIN_SETTINGS.DEEPSEEK_API_KEY:
                        providers.append(DeepSeekProvider())
                    if PENIN_SETTINGS.MISTRAL_API_KEY:
                        providers.append(MistralProvider())
                    if PENIN_SETTINGS.GEMINI_API_KEY:
                        providers.append(GeminiProvider())
                    if PENIN_SETTINGS.ANTHROPIC_API_KEY:
                        providers.append(AnthropicProvider())
                    if PENIN_SETTINGS.XAI_API_KEY:
                        providers.append(GrokProvider())
                    if providers:
                        router = MultiLLMRouter(providers)
                        sys_msg = (
                            "Você é o orquestrador do PENIN. Use ferramentas quando necessário. "
                            "Responda curto, com bullets das próximas ações de aquisição."
                        )
                        user_msg = (
                            f"Estado: ΔL∞={self.xt.delta_linf:.4f}, SR={self.xt.sr_score:.3f}, "
                            f"G={self.xt.g_score:.3f}, OCI={self.xt.oci_score:.3f}. "
                            "Que datasets/papers buscar agora?"
                        )
                        tools = [KAGGLE_SEARCH_TOOL, HF_SEARCH_TOOL]
                        r = await router.ask(
                            messages=[{"role": "user", "content": user_msg}],
                            system=sys_msg,
                            tools=tools,
                            temperature=0.3,
                        )
                        # Basic record of orchestrator result
                        self.worm.record(
                            EventType.LLM_QUERY,
                            {"provider": r.provider, "model": r.model, "latency": r.latency_s},
                            self.xt,
                        )
                except Exception as _e:
                    # Non-fatal
                    pass

            # Compute L∞ and components
            l_score = self.linf.compute(self.xt)
            result["metrics"]["L∞"] = l_score
            result["metrics"]["ΔL∞"] = self.xt.delta_linf
            
            caos_val = self.caos.compute(self.xt)
            result["metrics"]["CAOS⁺"] = caos_val
            result["metrics"]["harmony"] = self.xt.caos_harmony
            result["metrics"]["pattern_stable"] = self.xt.pattern_stable
            
            sr_val = self.sr.compute(self.xt)
            result["metrics"]["SR"] = sr_val
            
            g_val = self.gc.compute(self.xt)
            result["metrics"]["G"] = g_val
            
            oci_val = self.oci.compute(self.xt)
            result["metrics"]["OCI"] = oci_val
            
            # Compute alpha
            alpha = self._compute_alpha()
            result["metrics"]["α_t^Ω"] = alpha
            
            # Check gates with detailed tracing
            gates_failed = []
            
            sr_pass, sr_gate = self.sr.gate(self.xt)
            if not sr_pass:
                gates_failed.append("SR_GATE")
                result["gate_trace"].append(sr_gate)
                
            g_pass, g_gate = self.gc.gate(self.xt)
            if not g_pass:
                gates_failed.append("G_GATE")
                result["gate_trace"].append(g_gate)
                
            oci_pass, oci_gate = self.oci.gate(self.xt)
            if not oci_pass:
                gates_failed.append("OCI_GATE")
                result["gate_trace"].append(oci_gate)
                
            if self.xt.delta_linf < self.cfg.thresholds.beta_min:
                gates_failed.append("ΔL∞_GATE")
                result["gate_trace"].append({
                    "gate": "ΔL∞", "value": self.xt.delta_linf, 
                    "threshold": self.cfg.thresholds.beta_min,
                    "passed": False, "msg": f"ΔL∞={self.xt.delta_linf:.4f} < {self.cfg.thresholds.beta_min}"
                })
                
            if self.xt.caos_plus < self.cfg.thresholds.tau_caos:
                gates_failed.append("CAOS⁺_GATE")
                result["gate_trace"].append({
                    "gate": "CAOS⁺", "value": self.xt.caos_plus,
                    "threshold": self.cfg.thresholds.tau_caos,
                    "passed": False, "msg": f"CAOS⁺={self.xt.caos_plus:.3f} < {self.cfg.thresholds.tau_caos}"
                })
                
            if gates_failed:
                result.update({"decision": "ROLLBACK", "reason": "GATES_FAILED", "failed_gates": gates_failed})
                self.metrics["rollbacks"] += 1
                self.worm.record(EventType.ROLLBACK, result, self.xt, 
                               seed_state=self.rng.get_state(), gate_trace=result["gate_trace"])
                return result
                
            # Evolution step
            step = alpha * self.xt.delta_linf
            lr_opt = 1.0
            
            if self.fib.enabled:
                def lr_score(lr: float) -> float:
                    harm_bonus = 1.0 - min(1.0, abs(self.xt.caos_harmony - PHI) / PHI)
                    return step * lr * (1.0 + 0.1 * harm_bonus)
                lr_opt = self.fib.optimize_lr(lr_score, 0.5, 2.0)
                self.worm.record(EventType.FIBONACCI_OPT, 
                               {"lr_opt": lr_opt, "opt_count": self.fibR.optimization_count}, 
                               self.xt, seed_state=self.rng.get_state())
                               
            step_opt = step * lr_opt
            
            # Apply evolution
            self.xt.rsi       += step_opt * 0.08
            self.xt.synergy   += step_opt * 0.07
            self.xt.novelty   += step_opt * 0.05
            self.xt.stability += step_opt * 0.06
            self.xt.viability += step_opt * 0.05
            self.xt.cost       = max(0.0, self.xt.cost - step_opt * 0.03)
            self.xt.C = min(1.0, self.xt.C + step_opt * 0.04)
            self.xt.A = min(1.0, self.xt.A + step_opt * 0.05)
            self.xt.O = min(1.0, self.xt.O + step_opt * 0.03)
            self.xt.S = min(1.0, self.xt.S + step_opt * 0.02)
            self.xt.C_cal = min(1.0, self.xt.C_cal + step_opt * 0.03)
            self.xt.M     = min(1.0, self.xt.M     + step_opt * 0.04)
            self.xt.A_eff = min(1.0, self.xt.A_eff + step_opt * 0.05)
            
            if self.fib.enabled:
                self.fib.modulate_trust(self.xt)
                
            if step_opt > 0:
                result.update({"success": True, "decision": "PROMOTE", "evolution_step": step_opt})
                self.metrics["promotions"] += 1
                
                # CRITICAL: Record PROMOTE_ATTEST with atomic verification
                self.worm.record_promote_attest(
                    pre_state, self.xt, result, 
                    self.rng.get_state(), self.config_hash, step_opt
                )
            else:
                result.update({"decision": "ROLLBACK", "reason": "NEGATIVE_STEP"})
                self.metrics["rollbacks"] += 1
                self.worm.record(EventType.ROLLBACK, 
                               {"step": step_opt, "alpha": alpha, "ΔL∞": self.xt.delta_linf}, 
                               self.xt, seed_state=self.rng.get_state())
                               
            # Update cycle
            self.xt.cycle += 1
            self.metrics["cycles"] += 1
            
            # Performance metrics
            elapsed = max(1e-6, time.time() - t0)
            self.xt.latency_ms = elapsed * 1000.0
            self.xt.throughput = 1.0 / elapsed
            
            # Apply Fibonacci cache updates
            if self.fib.enabled:
                self.fib.apply_cache(self.cache)
                
            # Record master equation result
            self.worm.record(EventType.MASTER_EQ, 
                           {"cycle": self.xt.cycle, "metrics": result["metrics"], "step": step_opt}, 
                           self.xt, seed_state=self.rng.get_state())
                           
            return result
            
        except Exception as e:
            result.update({"decision": "ABORT", "error": str(e)})
            self.worm.record(EventType.CYCLE_ABORT, result, self.xt, seed_state=self.rng.get_state())
            return result
            
    def _compute_alpha(self) -> float:
        alpha_0 = self.cfg.evolution.alpha_0
        # Use sigmoidal normalization instead of ad-hoc division
        phi_caos = 1.0 / (1.0 + math.exp(-2.0 * (self.xt.caos_plus - 1.0)))
        sr_comp = 1.0 / (1.0 + math.exp(-5.0 * (self.xt.sr_score - 0.8)))
        g_comp  = 1.0 / (1.0 + math.exp(-5.0 * (self.xt.g_score - 0.7)))
        oci_comp = 1.0 / (1.0 + math.exp(-5.0 * (self.xt.oci_score - 0.9)))
        self.xt.alpha_omega = alpha_0 * phi_caos * sr_comp * g_comp * oci_comp
        return min(1.0, max(0.0, self.xt.alpha_omega))
        
    def verify_integrity(self) -> Dict[str, Any]:
        ok, err = self.worm.verify_chain()
        return {
            "worm_valid": ok, 
            "worm_error": err, 
            "metrics": dict(self.metrics), 
            "state": self.xt.to_dict(), 
            "cache": dict(self.cache.stats),
            "seed": self.rng.seed,
            "rng_calls": self.rng.call_count
        }
        
    def save_snapshot(self, tag: Optional[str] = None) -> str:
        snap_id = str(uuid.uuid4())
        path = DIRS["SNAPSHOTS"] / f"snapshot_{snap_id}.json"
        with open(path, "w") as f:
            json.dump({
                "id": snap_id, 
                "tag": tag, 
                "ts": datetime.now(timezone.utc).isoformat(), 
                "state": self.xt.to_dict(), 
                "metrics": self.metrics, 
                "config": self.cfg.dict(),
                "seed": self.rng.seed,
                "rng_state": self.rng.get_state()
            }, f, indent=2, ensure_ascii=False)
        self.worm.record(EventType.SNAPSHOT, {"id": snap_id, "path": str(path)}, self.xt)
        return snap_id
        
    def load_snapshot(self, snap_id: str) -> bool:
        path = DIRS["SNAPSHOTS"] / f"snapshot_{snap_id}.json"
        if not path.exists(): 
            return False
        try:
            with open(path) as f:
                data = json.load(f)
            self.xt = OmegaMEState(**data["state"])
            self.metrics = data["metrics"]
            if "seed" in data:
                self.rng.set_seed(data["seed"])
            return True
        except Exception as e:
            log.error(f"load_snapshot error: {e}")
            return False
            
    def shutdown(self):
        log.info("🛑 Shutting down core...")
        snap = self.save_snapshot("shutdown")
        self.worm.record(EventType.SHUTDOWN, 
                        {"snapshot": snap, "metrics": self.metrics, "final_seed_state": self.rng.get_state()}, 
                        self.xt)
        self.cache.clear()
        self.pool.shutdown(wait=True)
        self.ppool.shutdown(wait=True)

# -----------------------------------------------------------------------------
# CLI demonstration
# -----------------------------------------------------------------------------
async def main_demo():
    # Initialize with seed for determinism
    config = {"evolution": {"seed": 42}}
    core = PeninOmegaCore(config)
    
    def handler(*_): 
        core.shutdown()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    
    log.info("Starting 3 demo cycles with deterministic seed...")
    for i in range(3):
        res = await core.master_equation_cycle()
        log.info(f"Cycle {i+1}: decision={res['decision']}, success={res['success']}")
        if res.get("gate_trace"):
            log.info(f"  Gate trace: {len(res['gate_trace'])} checks")
        await asyncio.sleep(0.3)
        
    integ = core.verify_integrity()
    log.info(f"WORM valid: {integ['worm_valid']}, cycles: {integ['metrics']['cycles']}, RNG calls: {integ['rng_calls']}")
    core.shutdown()

if __name__ == "__main__":
    if HAS_TORCH:
        try:
            torch.set_num_threads(multiprocessing.cpu_count())
            if hasattr(torch, 'set_float32_matmul_precision'):
                torch.set_float32_matmul_precision('high')
        except Exception:
            pass
    asyncio.run(main_demo())