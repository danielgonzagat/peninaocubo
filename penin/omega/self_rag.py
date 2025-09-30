"""
Self-RAG Recursive System
=========================

Implements recursive self-RAG for knowledge management and self-reflection.
Uses lightweight text processing without heavy dependencies.
"""

import os
import re
import json
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class KnowledgeEntry:
    """Entry in the knowledge base"""
    name: str
    content: str
    timestamp: float
    source: str = "self_rag"
    tags: List[str] = None
    relevance_score: float = 0.0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class SelfRAGEngine:
    """Self-RAG engine for recursive knowledge management"""
    
    def __init__(self, knowledge_dir: str = None):
        if knowledge_dir is None:
            knowledge_dir = os.getenv("PENIN_ROOT", str(Path.home() / ".penin_omega"))
        
        self.knowledge_dir = Path(knowledge_dir) / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        self.knowledge_base: Dict[str, KnowledgeEntry] = {}
        self.query_history: List[Dict[str, Any]] = []
        self.reflection_history: List[Dict[str, Any]] = []
        
        # Load existing knowledge
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load existing knowledge base"""
        for txt_file in self.knowledge_dir.glob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                entry = KnowledgeEntry(
                    name=txt_file.stem,
                    content=content,
                    timestamp=txt_file.stat().st_mtime,
                    source="file"
                )
                
                self.knowledge_base[entry.name] = entry
            except Exception as e:
                print(f"Error loading {txt_file}: {e}")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Extract words and numbers
        tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
        return [t for t in tokens if len(t) > 1]  # Filter single characters
    
    def _compute_relevance(self, query_tokens: Counter, doc_tokens: Counter) -> float:
        """Compute relevance score between query and document"""
        if not query_tokens or not doc_tokens:
            return 0.0
        
        # Jaccard similarity
        intersection = sum(min(query_tokens[k], doc_tokens[k]) for k in query_tokens.keys())
        union = sum(max(query_tokens[k], doc_tokens[k]) for k in set(query_tokens.keys()) | set(doc_tokens.keys()))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def ingest_text(self, name: str, text: str, source: str = "self_rag", tags: List[str] = None) -> bool:
        """Ingest text into knowledge base"""
        try:
            entry = KnowledgeEntry(
                name=name,
                content=text,
                timestamp=time.time(),
                source=source,
                tags=tags or []
            )
            
            # Save to file
            file_path = self.knowledge_dir / f"{name}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Add to knowledge base
            self.knowledge_base[name] = entry
            
            return True
        except Exception as e:
            print(f"Error ingesting {name}: {e}")
            return False
    
    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query knowledge base"""
        query_tokens = Counter(self._tokenize(query_text))
        
        if not query_tokens:
            return []
        
        # Score all documents
        scored_docs = []
        for name, entry in self.knowledge_base.items():
            doc_tokens = Counter(self._tokenize(entry.content))
            relevance = self._compute_relevance(query_tokens, doc_tokens)
            
            if relevance > 0:
                scored_docs.append({
                    "name": name,
                    "content": entry.content,
                    "relevance": relevance,
                    "source": entry.source,
                    "tags": entry.tags,
                    "timestamp": entry.timestamp
                })
        
        # Sort by relevance
        scored_docs.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Record query
        query_record = {
            "timestamp": time.time(),
            "query": query_text,
            "results_count": len(scored_docs),
            "top_relevance": scored_docs[0]["relevance"] if scored_docs else 0.0
        }
        self.query_history.append(query_record)
        
        return scored_docs[:top_k]
    
    def self_cycle(self, base_question: str = None) -> Dict[str, Any]:
        """Perform self-reflection cycle"""
        if base_question is None:
            base_question = "What are the key insights for improving PENIN-Ω evolution?"
        
        # Query knowledge base
        results = self.query(base_question, top_k=3)
        
        if not results:
            return {
                "question": base_question,
                "answer": "No relevant knowledge found",
                "follow_up": "Consider ingesting more knowledge",
                "cycle_complete": False
            }
        
        # Generate follow-up question based on best result
        best_result = results[0]
        follow_up = self._generate_follow_up(base_question, best_result)
        
        # Perform follow-up query
        follow_up_results = self.query(follow_up, top_k=2)
        
        # Synthesize answer
        answer = self._synthesize_answer(results, follow_up_results)
        
        # Record reflection
        reflection_record = {
            "timestamp": time.time(),
            "base_question": base_question,
            "follow_up": follow_up,
            "results_count": len(results),
            "follow_up_results_count": len(follow_up_results),
            "answer_length": len(answer)
        }
        self.reflection_history.append(reflection_record)
        
        return {
            "question": base_question,
            "answer": answer,
            "follow_up": follow_up,
            "sources": [r["name"] for r in results],
            "cycle_complete": True
        }
    
    def _generate_follow_up(self, base_question: str, best_result: Dict[str, Any]) -> str:
        """Generate follow-up question based on best result"""
        content = best_result["content"]
        
        # Extract key concepts from content
        tokens = self._tokenize(content)
        token_counts = Counter(tokens)
        
        # Get most frequent meaningful tokens
        common_tokens = [t for t, count in token_counts.most_common(5) if count > 1]
        
        if common_tokens:
            follow_up = f"Elaborate on {', '.join(common_tokens[:3])} in context of {base_question}"
        else:
            follow_up = f"Provide more details about the concepts mentioned in: {content[:100]}..."
        
        return follow_up
    
    def _synthesize_answer(self, results: List[Dict[str, Any]], 
                          follow_up_results: List[Dict[str, Any]]) -> str:
        """Synthesize answer from query results"""
        all_results = results + follow_up_results
        
        if not all_results:
            return "No information available"
        
        # Combine content from top results
        combined_content = []
        for result in all_results[:3]:  # Top 3 results
            content = result["content"]
            # Truncate long content
            if len(content) > 200:
                content = content[:200] + "..."
            combined_content.append(content)
        
        # Simple synthesis
        synthesis = "Based on available knowledge:\n\n"
        for i, content in enumerate(combined_content, 1):
            synthesis += f"{i}. {content}\n\n"
        
        return synthesis.strip()
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        total_content = sum(len(entry.content) for entry in self.knowledge_base.values())
        
        return {
            "entries": len(self.knowledge_base),
            "total_content_length": total_content,
            "avg_content_length": total_content / len(self.knowledge_base) if self.knowledge_base else 0,
            "queries": len(self.query_history),
            "reflections": len(self.reflection_history),
            "knowledge_dir": str(self.knowledge_dir)
        }
    
    def search_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Search knowledge base by tags"""
        results = []
        
        for name, entry in self.knowledge_base.items():
            if any(tag in entry.tags for tag in tags):
                results.append({
                    "name": name,
                    "content": entry.content,
                    "tags": entry.tags,
                    "source": entry.source,
                    "timestamp": entry.timestamp
                })
        
        return results
    
    def cleanup_old_entries(self, max_age_days: int = 30):
        """Clean up old knowledge entries"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        to_remove = []
        for name, entry in self.knowledge_base.items():
            if entry.timestamp < cutoff_time and entry.source == "self_rag":
                to_remove.append(name)
        
        for name in to_remove:
            # Remove from knowledge base
            del self.knowledge_base[name]
            
            # Remove file
            file_path = self.knowledge_dir / f"{name}.txt"
            if file_path.exists():
                file_path.unlink()
        
        return len(to_remove)


# Integration with Life Equation
def integrate_self_rag_in_life_equation(
    life_verdict: Dict[str, Any],
    rag_engine: SelfRAGEngine = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Integrate self-RAG into Life Equation evaluation
    
    Args:
        life_verdict: Result from life_equation()
        rag_engine: Self-RAG engine instance
        
    Returns:
        (insight, rag_details)
    """
    if rag_engine is None:
        rag_engine = SelfRAGEngine()
    
    # Generate insight based on life verdict
    if life_verdict.get("ok", False):
        insight_query = "What insights can improve system evolution and alpha_eff?"
    else:
        insight_query = "What are common causes of evolution failure and how to address them?"
    
    # Perform self-reflection cycle
    cycle_result = rag_engine.self_cycle(insight_query)
    
    # Ingest current life verdict as knowledge
    verdict_text = f"""
    Life Equation Evaluation:
    - Status: {'PASS' if life_verdict.get('ok') else 'FAIL'}
    - Alpha Effective: {life_verdict.get('alpha_eff', 0.0)}
    - CAOS Phi: {life_verdict.get('metrics', {}).get('phi', 0.0)}
    - SR Score: {life_verdict.get('metrics', {}).get('sr', 0.0)}
    - Global Coherence: {life_verdict.get('metrics', {}).get('G', 0.0)}
    - Timestamp: {life_verdict.get('timestamp', time.time())}
    """
    
    rag_engine.ingest_text(
        f"life_verdict_{int(time.time())}",
        verdict_text,
        source="life_equation",
        tags=["life_equation", "evolution", "alpha_eff"]
    )
    
    rag_details = {
        "insight": cycle_result["answer"],
        "question": cycle_result["question"],
        "follow_up": cycle_result["follow_up"],
        "sources": cycle_result["sources"],
        "knowledge_stats": rag_engine.get_knowledge_stats()
    }
    
    return cycle_result["answer"], rag_details


# Example usage
if __name__ == "__main__":
    import os
    
    # Create self-RAG engine
    rag = SelfRAGEngine()
    
    # Ingest some knowledge
    rag.ingest_text(
        "evolution_principles",
        "Evolution requires careful balance of exploration and exploitation. Too much exploration leads to instability, too little leads to stagnation.",
        tags=["evolution", "balance", "exploration"]
    )
    
    rag.ingest_text(
        "alpha_optimization",
        "Alpha effective should be modulated by system coherence and risk metrics. Higher coherence allows for larger alpha values.",
        tags=["alpha", "optimization", "coherence"]
    )
    
    # Query knowledge
    results = rag.query("How to optimize alpha for evolution?")
    print(f"Query results: {len(results)}")
    for result in results:
        print(f"- {result['name']}: {result['relevance']:.3f}")
    
    # Self-reflection cycle
    cycle = rag.self_cycle("What are the key principles for safe evolution?")
    print(f"Self-reflection: {cycle['answer'][:100]}...")
    
    # Stats
    stats = rag.get_knowledge_stats()
    print(f"Knowledge stats: {stats}")