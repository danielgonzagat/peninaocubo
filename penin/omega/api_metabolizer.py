"""
API Metabolizer - I/O Recorder + Replayer
==========================================

Records API calls and responses for dependency reduction.
Implements replay mechanism to reduce external API dependencies.
"""

import orjson
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CallType(Enum):
    """API call types"""
    CHAT_COMPLETION = "chat_completion"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image_generation"
    FUNCTION_CALL = "function_call"
    DATA_FETCH = "data_fetch"


@dataclass
class APICall:
    """API call record"""
    call_id: str
    provider: str
    endpoint: str
    call_type: CallType
    request: Dict[str, Any]
    response: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    cost_usd: float = 0.0
    latency_s: float = 0.0
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "call_type": self.call_type.value,
            "request": self.request,
            "response": self.response,
            "timestamp": self.timestamp,
            "cost_usd": self.cost_usd,
            "latency_s": self.latency_s,
            "success": self.success
        }


class APIMetabolizer:
    """API metabolizer for recording and replaying calls"""
    
    def __init__(self, log_path: Optional[str] = None):
        if log_path is None:
            root_path = Path.home() / ".penin_omega" / "knowledge"
            root_path.mkdir(parents=True, exist_ok=True)
            self.log_path = root_path / "api_io.jsonl"
        else:
            self.log_path = Path(log_path)
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.call_history: List[APICall] = []
        self.replay_cache: Dict[str, APICall] = {}
        self.call_counter = 0
        
        # Load existing history
        self._load_history()
    
    def _load_history(self) -> None:
        """Load existing call history"""
        if not self.log_path.exists():
            return
        
        try:
            with open(self.log_path, 'rb') as f:
                for line in f:
                    if line.strip():
                        call_data = orjson.loads(line)
                        call = APICall(
                            call_id=call_data["call_id"],
                            provider=call_data["provider"],
                            endpoint=call_data["endpoint"],
                            call_type=CallType(call_data["call_type"]),
                            request=call_data["request"],
                            response=call_data["response"],
                            timestamp=call_data["timestamp"],
                            cost_usd=call_data.get("cost_usd", 0.0),
                            latency_s=call_data.get("latency_s", 0.0),
                            success=call_data.get("success", True)
                        )
                        self.call_history.append(call)
                        self.replay_cache[call.call_id] = call
        except Exception as e:
            print(f"Warning: Failed to load API history: {e}")
    
    def _save_call(self, call: APICall) -> None:
        """Save call to log file"""
        with open(self.log_path, 'ab') as f:
            f.write(orjson.dumps(call.to_dict()) + b'\n')
    
    def _generate_call_id(self, provider: str, endpoint: str, request: Dict[str, Any]) -> str:
        """Generate unique call ID"""
        # Create hash from provider, endpoint, and request
        request_str = orjson.dumps(request, option=orjson.OPT_SORT_KEYS).decode()
        hash_input = f"{provider}:{endpoint}:{request_str}"
        request_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        
        self.call_counter += 1
        return f"call_{self.call_counter:06d}_{request_hash}"
    
    def record_call(
        self,
        provider: str,
        endpoint: str,
        request: Dict[str, Any],
        response: Dict[str, Any],
        call_type: CallType = CallType.CHAT_COMPLETION,
        cost_usd: float = 0.0,
        latency_s: float = 0.0,
        success: bool = True
    ) -> str:
        """
        Record API call
        
        Args:
            provider: API provider (e.g., "openai", "anthropic")
            endpoint: API endpoint
            request: Request data
            response: Response data
            call_type: Type of call
            cost_usd: Cost in USD
            latency_s: Latency in seconds
            success: Whether call was successful
            
        Returns:
            Call ID
        """
        call_id = self._generate_call_id(provider, endpoint, request)
        
        call = APICall(
            call_id=call_id,
            provider=provider,
            endpoint=endpoint,
            call_type=call_type,
            request=request,
            response=response,
            cost_usd=cost_usd,
            latency_s=latency_s,
            success=success
        )
        
        # Store call
        self.call_history.append(call)
        self.replay_cache[call_id] = call
        
        # Save to file
        self._save_call(call)
        
        return call_id
    
    def suggest_replay(self, provider: str, endpoint: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Suggest replay for similar request
        
        Args:
            provider: API provider
            endpoint: API endpoint
            request: Request data
            
        Returns:
            Suggested response or None
        """
        # Find similar calls
        similar_calls = []
        
        for call in self.call_history:
            if call.provider == provider and call.endpoint == endpoint:
                similarity = self._calculate_similarity(request, call.request)
                if similarity > 0.8:  # High similarity threshold
                    similar_calls.append((call, similarity))
        
        if not similar_calls:
            return None
        
        # Sort by similarity and return best match
        similar_calls.sort(key=lambda x: x[1], reverse=True)
        best_call, similarity = similar_calls[0]
        
        return {
            "call_id": best_call.call_id,
            "similarity": similarity,
            "response": best_call.response,
            "timestamp": best_call.timestamp,
            "cost_saved": best_call.cost_usd
        }
    
    def _calculate_similarity(self, req1: Dict[str, Any], req2: Dict[str, Any]) -> float:
        """Calculate similarity between requests"""
        # Simple similarity based on key overlap
        keys1 = set(req1.keys())
        keys2 = set(req2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)
        
        if union == 0:
            return 0.0
        
        # Base similarity from key overlap
        key_similarity = intersection / union
        
        # Check for exact matches in common keys
        exact_matches = 0
        for key in keys1 & keys2:
            if req1[key] == req2[key]:
                exact_matches += 1
        
        # Weighted similarity
        if intersection > 0:
            exact_similarity = exact_matches / intersection
            return 0.7 * key_similarity + 0.3 * exact_similarity
        else:
            return key_similarity
    
    def get_replay_stats(self) -> Dict[str, Any]:
        """Get replay statistics"""
        if not self.call_history:
            return {"total_calls": 0, "total_cost": 0.0, "providers": {}}
        
        total_calls = len(self.call_history)
        total_cost = sum(call.cost_usd for call in self.call_history)
        
        # Provider stats
        provider_stats = {}
        for call in self.call_history:
            provider = call.provider
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "calls": 0,
                    "cost": 0.0,
                    "endpoints": set()
                }
            
            provider_stats[provider]["calls"] += 1
            provider_stats[provider]["cost"] += call.cost_usd
            provider_stats[provider]["endpoints"].add(call.endpoint)
        
        # Convert sets to lists for JSON serialization
        for provider_data in provider_stats.values():
            provider_data["endpoints"] = list(provider_data["endpoints"])
        
        return {
            "total_calls": total_calls,
            "total_cost": total_cost,
            "providers": provider_stats,
            "avg_cost_per_call": total_cost / total_calls if total_calls > 0 else 0.0
        }
    
    def search_calls(
        self,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
        call_type: Optional[CallType] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        limit: int = 100
    ) -> List[APICall]:
        """Search calls by criteria"""
        results = []
        
        for call in self.call_history:
            # Apply filters
            if provider and call.provider != provider:
                continue
            if endpoint and call.endpoint != endpoint:
                continue
            if call_type and call.call_type != call_type:
                continue
            if min_cost is not None and call.cost_usd < min_cost:
                continue
            if max_cost is not None and call.cost_usd > max_cost:
                continue
            
            results.append(call)
            
            if len(results) >= limit:
                break
        
        return results
    
    def export_history(self, filepath: str) -> None:
        """Export call history"""
        export_data = {
            "exported_at": time.time(),
            "total_calls": len(self.call_history),
            "calls": [call.to_dict() for call in self.call_history],
            "stats": self.get_replay_stats()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            orjson.dump(export_data, f, option=orjson.OPT_INDENT_2)
    
    def clear_history(self) -> None:
        """Clear call history"""
        self.call_history.clear()
        self.replay_cache.clear()
        
        # Remove log file
        if self.log_path.exists():
            try:
                self.log_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to remove log file: {e}")


class APIDecorator:
    """Decorator for automatic API call recording"""
    
    def __init__(self, metabolizer: APIMetabolizer):
        self.metabolizer = metabolizer
    
    def record_call(self, provider: str, endpoint: str, call_type: CallType = CallType.CHAT_COMPLETION):
        """Decorator for recording API calls"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Record successful call
                    latency = time.time() - start_time
                    call_id = self.metabolizer.record_call(
                        provider=provider,
                        endpoint=endpoint,
                        request={"args": args, "kwargs": kwargs},
                        response={"result": result},
                        call_type=call_type,
                        latency_s=latency,
                        success=True
                    )
                    
                    return result
                    
                except Exception as e:
                    # Record failed call
                    latency = time.time() - start_time
                    self.metabolizer.record_call(
                        provider=provider,
                        endpoint=endpoint,
                        request={"args": args, "kwargs": kwargs},
                        response={"error": str(e)},
                        call_type=call_type,
                        latency_s=latency,
                        success=False
                    )
                    
                    raise
            
            return wrapper
        return decorator


# Global metabolizer instance
_global_metabolizer: Optional[APIMetabolizer] = None


def get_global_metabolizer() -> APIMetabolizer:
    """Get global API metabolizer instance"""
    global _global_metabolizer
    
    if _global_metabolizer is None:
        _global_metabolizer = APIMetabolizer()
    
    return _global_metabolizer


def record_call(provider: str, endpoint: str, req: Dict[str, Any], resp: Dict[str, Any]) -> str:
    """Convenience function to record call"""
    metabolizer = get_global_metabolizer()
    return metabolizer.record_call(provider, endpoint, req, resp)


def suggest_replay(prompt: str) -> Optional[Dict[str, Any]]:
    """Convenience function to suggest replay"""
    metabolizer = get_global_metabolizer()
    
    # Create mock request for prompt
    request = {"prompt": prompt, "model": "gpt-4"}
    suggestion = metabolizer.suggest_replay("openai", "/v1/chat/completions", request)
    
    return suggestion


def test_api_metabolizer() -> Dict[str, Any]:
    """Test API metabolizer functionality"""
    metabolizer = get_global_metabolizer()
    
    # Clear existing history
    metabolizer.clear_history()
    
    # Record some test calls
    call1_id = metabolizer.record_call(
        provider="openai",
        endpoint="/v1/chat/completions",
        request={"prompt": "What is AI?", "model": "gpt-4"},
        response={"content": "AI is artificial intelligence..."},
        cost_usd=0.01,
        latency_s=1.2
    )
    
    call2_id = metabolizer.record_call(
        provider="openai",
        endpoint="/v1/chat/completions",
        request={"prompt": "What is machine learning?", "model": "gpt-4"},
        response={"content": "Machine learning is a subset of AI..."},
        cost_usd=0.015,
        latency_s=1.5
    )
    
    # Test replay suggestion
    suggestion = metabolizer.suggest_replay(
        "openai",
        "/v1/chat/completions",
        {"prompt": "What is AI?", "model": "gpt-4"}
    )
    
    # Get stats
    stats = metabolizer.get_replay_stats()
    
    # Search calls
    openai_calls = metabolizer.search_calls(provider="openai")
    
    return {
        "calls_recorded": 2,
        "call_ids": [call1_id, call2_id],
        "replay_suggestion": suggestion,
        "stats": stats,
        "openai_calls_found": len(openai_calls)
    }