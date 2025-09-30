"""
API Metabolizer - I/O Recorder and Replayer
===========================================

Implements API I/O recording and replaying for dependency reduction.
Enables learning from API interactions and gradual replacement.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class InteractionType(Enum):
    """Type of API interaction"""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class APIRecord:
    """Record of API interaction"""
    timestamp: float
    provider: str
    endpoint: str
    interaction_type: InteractionType
    request_data: Dict[str, Any] = field(default_factory=dict)
    response_data: Dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    latency_s: float = 0.0
    success: bool = True
    record_id: str = field(default_factory=lambda: str(int(time.time() * 1000)))


class APIMetabolizer:
    """API metabolizer for recording and replaying interactions"""
    
    def __init__(self, knowledge_dir: str = None):
        if knowledge_dir is None:
            knowledge_dir = os.getenv("PENIN_ROOT", str(Path.home() / ".penin_omega"))
        
        self.knowledge_dir = Path(knowledge_dir) / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        self.io_log_file = self.knowledge_dir / "api_io.jsonl"
        self.interaction_cache: Dict[str, List[APIRecord]] = {}
        self.replay_threshold = 0.8  # Similarity threshold for replay
        
        # Load existing records
        self._load_records()
    
    def _load_records(self):
        """Load existing API records"""
        if not self.io_log_file.exists():
            return
        
        try:
            with open(self.io_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        record_data = json.loads(line)
                        record = APIRecord(
                            timestamp=record_data["timestamp"],
                            provider=record_data["provider"],
                            endpoint=record_data["endpoint"],
                            interaction_type=InteractionType(record_data["interaction_type"]),
                            request_data=record_data.get("request_data", {}),
                            response_data=record_data.get("response_data", {}),
                            cost_usd=record_data.get("cost_usd", 0.0),
                            latency_s=record_data.get("latency_s", 0.0),
                            success=record_data.get("success", True),
                            record_id=record_data.get("record_id", "")
                        )
                        
                        # Cache by provider-endpoint
                        cache_key = f"{record.provider}:{record.endpoint}"
                        if cache_key not in self.interaction_cache:
                            self.interaction_cache[cache_key] = []
                        self.interaction_cache[cache_key].append(record)
        except Exception as e:
            print(f"Error loading API records: {e}")
    
    def _compute_request_hash(self, request_data: Dict[str, Any]) -> str:
        """Compute hash for request data"""
        # Create deterministic representation
        normalized = json.dumps(request_data, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _compute_similarity(self, req1: Dict[str, Any], req2: Dict[str, Any]) -> float:
        """Compute similarity between two requests"""
        # Simple similarity based on key overlap
        keys1 = set(req1.keys())
        keys2 = set(req2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        intersection = keys1.intersection(keys2)
        union = keys1.union(keys2)
        
        # Basic similarity
        key_similarity = len(intersection) / len(union)
        
        # Value similarity for common keys
        value_similarity = 0.0
        if intersection:
            for key in intersection:
                if req1[key] == req2[key]:
                    value_similarity += 1.0
            value_similarity /= len(intersection)
        
        # Combined similarity
        return 0.7 * key_similarity + 0.3 * value_similarity
    
    def record_call(self, provider: str, endpoint: str, request: Dict[str, Any], 
                   response: Dict[str, Any], cost_usd: float = 0.0, 
                   latency_s: float = 0.0, success: bool = True) -> str:
        """Record API call"""
        record = APIRecord(
            timestamp=time.time(),
            provider=provider,
            endpoint=endpoint,
            interaction_type=InteractionType.REQUEST,
            request_data=request,
            response_data=response,
            cost_usd=cost_usd,
            latency_s=latency_s,
            success=success
        )
        
        # Cache record
        cache_key = f"{provider}:{endpoint}"
        if cache_key not in self.interaction_cache:
            self.interaction_cache[cache_key] = []
        self.interaction_cache[cache_key].append(record)
        
        # Persist to file
        self._persist_record(record)
        
        return record.record_id
    
    def _persist_record(self, record: APIRecord):
        """Persist record to file"""
        try:
            record_data = {
                "timestamp": record.timestamp,
                "provider": record.provider,
                "endpoint": record.endpoint,
                "interaction_type": record.interaction_type.value,
                "request_data": record.request_data,
                "response_data": record.response_data,
                "cost_usd": record.cost_usd,
                "latency_s": record.latency_s,
                "success": record.success,
                "record_id": record.record_id
            }
            
            with open(self.io_log_file, 'a') as f:
                f.write(json.dumps(record_data) + '\n')
        except Exception as e:
            print(f"Error persisting API record: {e}")
    
    def suggest_replay(self, provider: str, endpoint: str, 
                      request: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Suggest replay for similar request
        
        Args:
            provider: API provider
            endpoint: API endpoint
            request: Request data
            
        Returns:
            (response_data, similarity_score)
        """
        cache_key = f"{provider}:{endpoint}"
        records = self.interaction_cache.get(cache_key, [])
        
        if not records:
            return None, 0.0
        
        # Find most similar request
        best_similarity = 0.0
        best_response = None
        
        for record in records:
            if not record.success:
                continue
            
            similarity = self._compute_similarity(request, record.request_data)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_response = record.response_data
        
        # Only suggest if similarity is above threshold
        if best_similarity >= self.replay_threshold:
            return best_response, best_similarity
        
        return None, best_similarity
    
    def get_usage_stats(self, provider: str = None, endpoint: str = None) -> Dict[str, Any]:
        """Get usage statistics"""
        total_calls = 0
        total_cost = 0.0
        total_latency = 0.0
        success_count = 0
        
        for cache_key, records in self.interaction_cache.items():
            if provider and not cache_key.startswith(f"{provider}:"):
                continue
            
            for record in records:
                if endpoint and record.endpoint != endpoint:
                    continue
                
                total_calls += 1
                total_cost += record.cost_usd
                total_latency += record.latency_s
                if record.success:
                    success_count += 1
        
        return {
            "total_calls": total_calls,
            "total_cost_usd": total_cost,
            "avg_latency_s": total_latency / total_calls if total_calls > 0 else 0.0,
            "success_rate": success_count / total_calls if total_calls > 0 else 0.0,
            "providers": list(set(r.provider for records in self.interaction_cache.values() for r in records)),
            "endpoints": list(set(r.endpoint for records in self.interaction_cache.values() for r in records))
        }
    
    def get_replay_candidates(self, min_similarity: float = 0.8) -> List[Dict[str, Any]]:
        """Get candidates for replay implementation"""
        candidates = []
        
        for cache_key, records in self.interaction_cache.items():
            provider, endpoint = cache_key.split(":", 1)
            
            # Group similar requests
            request_groups = {}
            for record in records:
                if not record.success:
                    continue
                
                req_hash = self._compute_request_hash(record.request_data)
                if req_hash not in request_groups:
                    request_groups[req_hash] = []
                request_groups[req_hash].append(record)
            
            # Find frequently used patterns
            for req_hash, group_records in request_groups.items():
                if len(group_records) >= 3:  # At least 3 similar calls
                    avg_cost = sum(r.cost_usd for r in group_records) / len(group_records)
                    avg_latency = sum(r.latency_s for r in group_records) / len(group_records)
                    
                    candidates.append({
                        "provider": provider,
                        "endpoint": endpoint,
                        "request_pattern": group_records[0].request_data,
                        "response_pattern": group_records[0].response_data,
                        "frequency": len(group_records),
                        "avg_cost_usd": avg_cost,
                        "avg_latency_s": avg_latency,
                        "replay_potential": avg_cost * len(group_records)  # Cost savings potential
                    })
        
        # Sort by replay potential
        candidates.sort(key=lambda x: x["replay_potential"], reverse=True)
        
        return candidates
    
    def cleanup_old_records(self, max_age_days: int = 30):
        """Clean up old API records"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        # Clean cache
        for cache_key, records in self.interaction_cache.items():
            self.interaction_cache[cache_key] = [
                r for r in records if r.timestamp >= cutoff_time
            ]
        
        # Clean file (simple approach - rewrite)
        if self.io_log_file.exists():
            try:
                with open(self.io_log_file, 'r') as f:
                    lines = f.readlines()
                
                filtered_lines = []
                for line in lines:
                    if line.strip():
                        record_data = json.loads(line)
                        if record_data["timestamp"] >= cutoff_time:
                            filtered_lines.append(line)
                
                with open(self.io_log_file, 'w') as f:
                    f.writelines(filtered_lines)
            except Exception as e:
                print(f"Error cleaning up records: {e}")


# Integration decorator for existing providers
def metabolize_api_call(metabolizer: APIMetabolizer, provider: str, endpoint: str):
    """Decorator to automatically record API calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract request data
            request_data = {
                "args": args,
                "kwargs": kwargs
            }
            
            start_time = time.time()
            try:
                # Make API call
                response = func(*args, **kwargs)
                latency = time.time() - start_time
                
                # Record successful call
                metabolizer.record_call(
                    provider=provider,
                    endpoint=endpoint,
                    request=request_data,
                    response=response,
                    latency_s=latency,
                    success=True
                )
                
                return response
            except Exception as e:
                latency = time.time() - start_time
                
                # Record failed call
                metabolizer.record_call(
                    provider=provider,
                    endpoint=endpoint,
                    request=request_data,
                    response={"error": str(e)},
                    latency_s=latency,
                    success=False
                )
                
                raise
        return wrapper
    return decorator


# Integration with Life Equation
def integrate_api_metabolizer_in_life_equation(
    life_verdict: Dict[str, Any],
    metabolizer: APIMetabolizer = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Integrate API metabolizer into Life Equation evaluation
    
    Args:
        life_verdict: Result from life_equation()
        metabolizer: API metabolizer instance
        
    Returns:
        (replay_suggestions, metabolizer_details)
    """
    if metabolizer is None:
        metabolizer = APIMetabolizer()
    
    # Get replay candidates
    candidates = metabolizer.get_replay_candidates()
    
    # Get usage stats
    stats = metabolizer.get_usage_stats()
    
    # Suggest replays for common patterns
    replay_suggestions = []
    for candidate in candidates[:5]:  # Top 5 candidates
        if candidate["replay_potential"] > 1.0:  # Significant cost savings
            replay_suggestions.append({
                "provider": candidate["provider"],
                "endpoint": candidate["endpoint"],
                "cost_savings_usd": candidate["replay_potential"],
                "frequency": candidate["frequency"],
                "avg_latency_s": candidate["avg_latency_s"]
            })
    
    metabolizer_details = {
        "replay_suggestions": replay_suggestions,
        "usage_stats": stats,
        "total_candidates": len(candidates),
        "metabolizer_active": True
    }
    
    return replay_suggestions, metabolizer_details


# Example usage
if __name__ == "__main__":
    import os
    
    # Create metabolizer
    metabolizer = APIMetabolizer()
    
    # Record some API calls
    metabolizer.record_call(
        provider="openai",
        endpoint="chat/completions",
        request={"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]},
        response={"choices": [{"message": {"content": "Hi there!"}}]},
        cost_usd=0.01,
        latency_s=1.2
    )
    
    # Suggest replay
    replay_response, similarity = metabolizer.suggest_replay(
        provider="openai",
        endpoint="chat/completions",
        request={"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}
    )
    
    print(f"Replay suggestion: {replay_response is not None}, similarity: {similarity:.3f}")
    
    # Get stats
    stats = metabolizer.get_usage_stats()
    print(f"Usage stats: {stats}")
    
    # Get candidates
    candidates = metabolizer.get_replay_candidates()
    print(f"Replay candidates: {len(candidates)}")