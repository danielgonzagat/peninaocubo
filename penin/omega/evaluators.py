"""
Evaluators Module - Suíte U/S/C/L
=================================

Implementa baterias de avaliação para:
- U (Utilidade): tarefas determinísticas com gabarito
- S (Estabilidade): ECE, robustez, calibração
- C (Custo): normalização por baseline, tokens, latência
- L (Aprendizado Futuro): heurísticas de reuso e composição

Todas as métricas são normalizadas para [0,1] e compostas via média harmônica.
"""

import re
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Callable
from typing_extensions import Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .scoring import harmonic_mean, normalize_series, ema_update
except ImportError:
    # Fallback para execução direta
    import sys
    sys.path.append('/workspace')
    from penin.omega.scoring import harmonic_mean, normalize_series, ema_update


class TaskType(Enum):
    """Tipos de tarefas de avaliação"""
    REGEX_TO_JSON = "regex_to_json"
    EXTRACT_FIELDS = "extract_fields"
    SHORT_SUMMARY = "short_summary"
    TABLE_TO_JSON = "table_to_json"
    CLASSIFICATION = "classification"
    QA_SIMPLE = "qa_simple"


@dataclass
class TaskResult:
    """Resultado de uma tarefa"""
    task_id: str
    task_type: TaskType
    input_data: str
    expected_output: Any
    actual_output: Any
    score: float
    metric_name: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "input_data": self.input_data[:100] + "..." if len(self.input_data) > 100 else self.input_data,
            "expected_output": self.expected_output,
            "actual_output": self.actual_output,
            "score": self.score,
            "metric_name": self.metric_name,
            "details": self.details
        }


@dataclass
class EvaluationResult:
    """Resultado completo de avaliação"""
    provider_id: str
    model_name: str
    config: Dict[str, Any]
    
    # Métricas U/S/C/L
    U: float  # Utilidade
    S: float  # Estabilidade
    C: float  # Custo
    L: float  # Aprendizado futuro
    
    # Métricas técnicas
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    
    # Detalhes das tarefas
    task_results: List[TaskResult]
    
    # Metadados
    timestamp: float
    duration_s: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "model_name": self.model_name,
            "config": self.config,
            "metrics": {
                "U": self.U,
                "S": self.S, 
                "C": self.C,
                "L": self.L
            },
            "technical": {
                "total_tokens": self.total_tokens,
                "total_cost_usd": self.total_cost_usd,
                "avg_latency_ms": self.avg_latency_ms
            },
            "task_results": [t.to_dict() for t in self.task_results],
            "metadata": {
                "timestamp": self.timestamp,
                "duration_s": self.duration_s,
                "n_tasks": len(self.task_results)
            }
        }


class UtilityEvaluator:
    """Avaliador de Utilidade (U) - tarefas determinísticas"""
    
    def __init__(self):
        self.tasks = self._create_tasks()
        
    def _create_tasks(self) -> List[Dict[str, Any]]:
        """Cria conjunto de tarefas determinísticas"""
        return [
            # Regex to JSON
            {
                "id": "regex_json_1",
                "type": TaskType.REGEX_TO_JSON,
                "input": "Nome: João Silva, Email: joao@email.com, Telefone: (11) 99999-9999",
                "expected": {"nome": "João Silva", "email": "joao@email.com", "telefone": "(11) 99999-9999"},
                "instruction": "Extraia nome, email e telefone em formato JSON"
            },
            # Field extraction
            {
                "id": "extract_1", 
                "type": TaskType.EXTRACT_FIELDS,
                "input": "Produto: Notebook Dell, Preço: R$ 2.500,00, Categoria: Eletrônicos",
                "expected": {"produto": "Notebook Dell", "preco": "R$ 2.500,00", "categoria": "Eletrônicos"},
                "instruction": "Extraia produto, preço e categoria"
            },
            # Short summary
            {
                "id": "summary_1",
                "type": TaskType.SHORT_SUMMARY,
                "input": "A inteligência artificial está transformando diversos setores da economia. Empresas estão investindo bilhões em IA para automatizar processos, melhorar a experiência do cliente e criar novos produtos. No entanto, também há preocupações sobre o impacto no emprego e a necessidade de regulamentação adequada.",
                "expected": "IA transforma economia com investimentos bilionários, mas gera preocupações sobre emprego e regulamentação.",
                "instruction": "Resuma em uma frase"
            },
            # Simple QA
            {
                "id": "qa_1",
                "type": TaskType.QA_SIMPLE,
                "input": "Qual é a capital do Brasil?",
                "expected": "Brasília",
                "instruction": "Responda diretamente"
            }
        ]
        
    def evaluate_task(self, task: Dict[str, Any], 
                     model_response: str) -> TaskResult:
        """Avalia uma tarefa específica"""
        task_type = task["type"]
        
        if task_type == TaskType.REGEX_TO_JSON:
            score = self._score_json_extraction(task["expected"], model_response)
            metric = "exact_match"
        elif task_type == TaskType.EXTRACT_FIELDS:
            score = self._score_field_extraction(task["expected"], model_response)
            metric = "field_f1"
        elif task_type == TaskType.SHORT_SUMMARY:
            score = self._score_summary(task["expected"], model_response)
            metric = "rouge_1"
        elif task_type == TaskType.QA_SIMPLE:
            score = self._score_qa(task["expected"], model_response)
            metric = "exact_match"
        else:
            score = 0.0
            metric = "unknown"
            
        return TaskResult(
            task_id=task["id"],
            task_type=task_type,
            input_data=task["input"],
            expected_output=task["expected"],
            actual_output=model_response,
            score=score,
            metric_name=metric,
            details={"instruction": task["instruction"]}
        )
        
    def _score_json_extraction(self, expected: Dict, response: str) -> float:
        """Score para extração JSON (exact match)"""
        try:
            # Tentar extrair JSON da resposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return 0.0
                
            actual = json.loads(json_match.group())
            
            # Exact match
            return 1.0 if actual == expected else 0.0
        except:
            return 0.0
            
    def _score_field_extraction(self, expected: Dict, response: str) -> float:
        """Score para extração de campos (F1)"""
        try:
            # Tentar extrair campos da resposta
            extracted = {}
            for key in expected.keys():
                # Buscar padrões como "key: value"
                pattern = rf"{key}[:\s]+([^\n,]+)"
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    extracted[key] = match.group(1).strip()
                    
            # Calcular F1
            if not extracted:
                return 0.0
                
            # Precision e Recall
            correct = sum(1 for k, v in extracted.items() 
                         if k in expected and expected[k].lower() in v.lower())
            precision = correct / len(extracted) if extracted else 0
            recall = correct / len(expected) if expected else 0
            
            if precision + recall == 0:
                return 0.0
                
            f1 = 2 * precision * recall / (precision + recall)
            return f1
        except:
            return 0.0
            
    def _score_summary(self, expected: str, response: str) -> float:
        """Score para resumo (ROUGE-1 simplificado)"""
        try:
            # Tokenizar (palavras simples)
            expected_words = set(expected.lower().split())
            response_words = set(response.lower().split())
            
            if not expected_words:
                return 1.0 if not response_words else 0.0
                
            # ROUGE-1 (overlap de palavras)
            overlap = len(expected_words & response_words)
            rouge_1 = overlap / len(expected_words)
            
            return min(1.0, rouge_1)
        except:
            return 0.0
            
    def _score_qa(self, expected: str, response: str) -> float:
        """Score para QA simples"""
        try:
            # Normalizar strings
            exp_norm = expected.lower().strip()
            resp_norm = response.lower().strip()
            
            # Exact match ou substring
            if exp_norm in resp_norm or resp_norm in exp_norm:
                return 1.0
            else:
                return 0.0
        except:
            return 0.0
            
    def evaluate_all(self, model_func: Callable[[str], str]) -> Tuple[float, List[TaskResult]]:
        """
        Avalia todas as tarefas de utilidade
        
        Args:
            model_func: Função que recebe prompt e retorna resposta
            
        Returns:
            (U_score, task_results)
        """
        results = []
        
        for task in self.tasks:
            # Criar prompt
            prompt = f"{task['instruction']}\n\nInput: {task['input']}\n\nOutput:"
            
            # Executar modelo
            try:
                response = model_func(prompt)
                result = self.evaluate_task(task, response)
            except Exception as e:
                result = TaskResult(
                    task_id=task["id"],
                    task_type=task["type"],
                    input_data=task["input"],
                    expected_output=task["expected"],
                    actual_output=f"ERROR: {e}",
                    score=0.0,
                    metric_name="error",
                    details={"error": str(e)}
                )
                
            results.append(result)
            
        # Calcular U via média harmônica
        scores = [r.score for r in results]
        U_score = harmonic_mean(scores) if scores else 0.0
        
        return U_score, results


class StabilityEvaluator:
    """Avaliador de Estabilidade (S) - ECE, robustez, calibração"""
    
    def __init__(self):
        self.perturbations = [
            "Adicione um ponto final.",
            "Mude para maiúsculas: ",
            "Reformule: ",
            "Em outras palavras: "
        ]
        
    def evaluate_ece_toy(self, model_func: Callable[[str], Tuple[str, float]],
                        test_prompts: List[str]) -> Tuple[float, Dict[str, Any]]:
        """
        Avalia ECE usando prompts de teste
        
        Args:
            model_func: Função que retorna (resposta, confiança)
            test_prompts: Lista de prompts para teste
            
        Returns:
            (ece_score, details)
        """
        confidences = []
        predictions = []
        labels = []
        
        for prompt in test_prompts:
            try:
                response, confidence = model_func(prompt)
                
                # Simular label (para demo, usar hash do prompt)
                label = 1 if hash(prompt) % 2 == 0 else 0
                prediction = 1 if "sim" in response.lower() or "yes" in response.lower() else 0
                
                confidences.append(confidence)
                predictions.append(prediction)
                labels.append(label)
                
            except Exception:
                continue
                
        if not confidences:
            return 1.0, {"error": "no_valid_responses"}
            
        # Calcular ECE simplificado (binning)
        try:
            from .ethics_metrics import ECECalculator
        except ImportError:
            from penin.omega.ethics_metrics import ECECalculator
        ece_calc = ECECalculator(n_bins=5)  # Menos bins para poucos dados
        
        try:
            ece, details = ece_calc.calculate(confidences, predictions, labels)
            # Converter ECE para score (menor ECE = melhor)
            ece_score = max(0.0, 1.0 - ece * 10)  # Scale ECE para [0,1]
            return ece_score, details
        except Exception as e:
            return 0.0, {"error": str(e)}
            
    def evaluate_robustness(self, model_func: Callable[[str], str],
                          base_prompts: List[str]) -> Tuple[float, Dict[str, Any]]:
        """
        Avalia robustez com perturbações
        
        Args:
            model_func: Função do modelo
            base_prompts: Prompts base para perturbar
            
        Returns:
            (robustness_score, details)
        """
        robustness_scores = []
        
        for base_prompt in base_prompts:
            try:
                # Resposta base
                base_response = model_func(base_prompt)
                
                # Respostas com perturbações
                perturbed_responses = []
                for perturbation in self.perturbations:
                    perturbed_prompt = perturbation + base_prompt
                    try:
                        perturbed_response = model_func(perturbed_prompt)
                        perturbed_responses.append(perturbed_response)
                    except:
                        continue
                        
                if not perturbed_responses:
                    continue
                    
                # Calcular similaridade (overlap de palavras)
                base_words = set(base_response.lower().split())
                similarities = []
                
                for perturbed in perturbed_responses:
                    perturbed_words = set(perturbed.lower().split())
                    if base_words or perturbed_words:
                        overlap = len(base_words & perturbed_words)
                        union = len(base_words | perturbed_words)
                        similarity = overlap / union if union > 0 else 0
                        similarities.append(similarity)
                        
                if similarities:
                    # Robustez = média das similaridades
                    prompt_robustness = sum(similarities) / len(similarities)
                    robustness_scores.append(prompt_robustness)
                    
            except Exception:
                continue
                
        if not robustness_scores:
            return 0.0, {"error": "no_valid_robustness_tests"}
            
        # Score final
        avg_robustness = sum(robustness_scores) / len(robustness_scores)
        
        details = {
            "n_prompts_tested": len(base_prompts),
            "n_valid_tests": len(robustness_scores),
            "avg_robustness": avg_robustness,
            "robustness_scores": robustness_scores
        }
        
        return avg_robustness, details
        
    def evaluate_stability(self, model_func: Callable[[str], str],
                          test_prompts: List[str]) -> Tuple[float, Dict[str, Any]]:
        """
        Avalia estabilidade geral (ECE + robustez)
        
        Returns:
            (S_score, details)
        """
        # Para demo, usar função simplificada sem confiança
        def simple_model_with_confidence(prompt):
            response = model_func(prompt)
            # Simular confiança baseada no tamanho da resposta
            confidence = min(0.95, len(response) / 100.0)
            return response, confidence
            
        # ECE
        ece_score, ece_details = self.evaluate_ece_toy(
            simple_model_with_confidence, test_prompts
        )
        
        # Robustez
        robustness_score, robustness_details = self.evaluate_robustness(
            model_func, test_prompts
        )
        
        # Combinar via média harmônica
        S_score = harmonic_mean([ece_score, robustness_score])
        
        details = {
            "ece_score": ece_score,
            "robustness_score": robustness_score,
            "ece_details": ece_details,
            "robustness_details": robustness_details,
            "combination_method": "harmonic_mean"
        }
        
        return S_score, details


class CostEvaluator:
    """Avaliador de Custo (C) - normalização por baseline"""
    
    def __init__(self, baseline_cost_usd: float = 0.01):
        self.baseline_cost = baseline_cost_usd
        
    def evaluate_cost(self, 
                     total_cost_usd: float,
                     total_tokens: int,
                     avg_latency_ms: float) -> Tuple[float, Dict[str, Any]]:
        """
        Avalia custo normalizado
        
        Args:
            total_cost_usd: Custo total em USD
            total_tokens: Tokens totais usados
            avg_latency_ms: Latência média
            
        Returns:
            (C_score, details) - onde C_score menor é melhor
        """
        # Normalizar custo por baseline
        cost_ratio = total_cost_usd / self.baseline_cost if self.baseline_cost > 0 else 1.0
        
        # Normalizar para [0,1] onde 0 = custo muito baixo, 1 = custo muito alto
        cost_normalized = min(1.0, cost_ratio)
        
        # Penalizar latência alta (>2s é ruim)
        latency_penalty = min(1.0, avg_latency_ms / 2000.0)  # 2s = penalty 1.0
        
        # Penalizar uso excessivo de tokens
        token_penalty = min(1.0, total_tokens / 10000.0)  # 10k tokens = penalty 1.0
        
        # Score final (média dos componentes de custo)
        C_score = (cost_normalized + latency_penalty + token_penalty) / 3.0
        
        details = {
            "total_cost_usd": total_cost_usd,
            "baseline_cost_usd": self.baseline_cost,
            "cost_ratio": cost_ratio,
            "cost_normalized": cost_normalized,
            "total_tokens": total_tokens,
            "avg_latency_ms": avg_latency_ms,
            "latency_penalty": latency_penalty,
            "token_penalty": token_penalty,
            "components": {
                "cost": cost_normalized,
                "latency": latency_penalty,
                "tokens": token_penalty
            }
        }
        
        return C_score, details


class LearningEvaluator:
    """Avaliador de Aprendizado Futuro (L) - heurísticas de reuso"""
    
    def __init__(self):
        self.heuristics = [
            "template_reuse",
            "tool_creation", 
            "knowledge_transfer",
            "efficiency_gain"
        ]
        
    def evaluate_learning_potential(self,
                                  responses: List[str],
                                  config: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Avalia potencial de aprendizado futuro
        
        Args:
            responses: Respostas do modelo
            config: Configuração usada
            
        Returns:
            (L_score, details)
        """
        scores = {}
        
        # 1. Template reuse (respostas seguem padrão)
        template_score = self._score_template_reuse(responses)
        scores["template_reuse"] = template_score
        
        # 2. Tool creation (menciona ferramentas/scripts)
        tool_score = self._score_tool_creation(responses)
        scores["tool_creation"] = tool_score
        
        # 3. Knowledge transfer (conecta conceitos)
        knowledge_score = self._score_knowledge_transfer(responses)
        scores["knowledge_transfer"] = knowledge_score
        
        # 4. Efficiency gain (respostas mais concisas/eficientes)
        efficiency_score = self._score_efficiency_gain(responses, config)
        scores["efficiency_gain"] = efficiency_score
        
        # Combinar via média harmônica
        L_score = harmonic_mean(list(scores.values()))
        
        details = {
            "heuristic_scores": scores,
            "combination_method": "harmonic_mean",
            "n_responses": len(responses)
        }
        
        return L_score, details
        
    def _score_template_reuse(self, responses: List[str]) -> float:
        """Score para reuso de template"""
        if len(responses) < 2:
            return 0.5  # Default
            
        # Calcular similaridade estrutural entre respostas
        similarities = []
        
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                # Similaridade baseada em estrutura (linhas, pontuação)
                r1_lines = len(responses[i].split('\n'))
                r2_lines = len(responses[j].split('\n'))
                
                r1_punct = len([c for c in responses[i] if c in '.,!?:;'])
                r2_punct = len([c for c in responses[j] if c in '.,!?:;'])
                
                # Similaridade estrutural
                line_sim = 1.0 - abs(r1_lines - r2_lines) / max(r1_lines, r2_lines, 1)
                punct_sim = 1.0 - abs(r1_punct - r2_punct) / max(r1_punct, r2_punct, 1)
                
                similarities.append((line_sim + punct_sim) / 2.0)
                
        return sum(similarities) / len(similarities) if similarities else 0.5
        
    def _score_tool_creation(self, responses: List[str]) -> float:
        """Score para criação de ferramentas"""
        tool_keywords = [
            "script", "função", "ferramenta", "automatizar",
            "código", "programa", "algoritmo", "implementar"
        ]
        
        tool_mentions = 0
        total_words = 0
        
        for response in responses:
            words = response.lower().split()
            total_words += len(words)
            
            for keyword in tool_keywords:
                tool_mentions += words.count(keyword)
                
        # Densidade de menções de ferramentas
        if total_words == 0:
            return 0.0
            
        density = tool_mentions / total_words
        return min(1.0, density * 100)  # Scale para [0,1]
        
    def _score_knowledge_transfer(self, responses: List[str]) -> float:
        """Score para transferência de conhecimento"""
        connection_keywords = [
            "similar", "como", "assim como", "por exemplo",
            "relacionado", "conecta", "aplica", "generaliza"
        ]
        
        connections = 0
        
        for response in responses:
            response_lower = response.lower()
            for keyword in connection_keywords:
                connections += response_lower.count(keyword)
                
        # Normalizar por número de respostas
        avg_connections = connections / len(responses) if responses else 0
        return min(1.0, avg_connections / 2.0)  # 2 conexões = score 1.0
        
    def _score_efficiency_gain(self, responses: List[str], config: Dict[str, Any]) -> float:
        """Score para ganho de eficiência"""
        if not responses:
            return 0.0
            
        # Eficiência = informação por token
        total_chars = sum(len(r) for r in responses)
        avg_chars = total_chars / len(responses)
        
        # Normalizar: 100 chars = score 0.5, 200 chars = score 1.0
        efficiency_score = min(1.0, avg_chars / 200.0)
        
        return efficiency_score


class ComprehensiveEvaluator:
    """Avaliador completo U/S/C/L"""
    
    def __init__(self, baseline_cost_usd: float = 0.01):
        self.utility_eval = UtilityEvaluator()
        self.stability_eval = StabilityEvaluator()
        self.cost_eval = CostEvaluator(baseline_cost_usd)
        self.learning_eval = LearningEvaluator()
        
    def evaluate_model(self,
                      model_func: Callable[[str], str],
                      config: Dict[str, Any],
                      provider_id: str = "unknown",
                      model_name: str = "unknown") -> EvaluationResult:
        """
        Avaliação completa U/S/C/L
        
        Args:
            model_func: Função do modelo
            config: Configuração usada
            provider_id: ID do provider
            model_name: Nome do modelo
            
        Returns:
            EvaluationResult completo
        """
        start_time = time.time()
        
        # Simular métricas técnicas (em produção, vem do provider)
        total_tokens = 0
        total_cost_usd = 0.0
        latencies = []
        
        # U: Utilidade
        U_score, utility_results = self.utility_eval.evaluate_all(model_func)
        
        # Simular métricas técnicas baseadas nas tarefas
        for result in utility_results:
            # Simular tokens baseado no tamanho da resposta
            response_tokens = len(str(result.actual_output).split())
            total_tokens += response_tokens
            
            # Simular custo (0.001 USD por token)
            task_cost = response_tokens * 0.001
            total_cost_usd += task_cost
            
            # Simular latência (50-200ms por tarefa)
            latency = 50 + hash(result.task_id) % 150
            latencies.append(latency)
            
        avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0
        
        # S: Estabilidade
        test_prompts = [task["input"] for task in self.utility_eval.tasks]
        S_score, stability_details = self.stability_eval.evaluate_stability(
            model_func, test_prompts
        )
        
        # C: Custo
        C_score, cost_details = self.cost_eval.evaluate_cost(
            total_cost_usd, total_tokens, avg_latency_ms
        )
        
        # L: Aprendizado futuro
        responses = [str(result.actual_output) for result in utility_results]
        L_score, learning_details = self.learning_eval.evaluate_learning_potential(
            responses, config
        )
        
        # Criar resultado
        duration_s = time.time() - start_time
        
        result = EvaluationResult(
            provider_id=provider_id,
            model_name=model_name,
            config=config,
            U=U_score,
            S=S_score,
            C=C_score,
            L=L_score,
            total_tokens=total_tokens,
            total_cost_usd=total_cost_usd,
            avg_latency_ms=avg_latency_ms,
            task_results=utility_results,
            timestamp=start_time,
            duration_s=duration_s
        )
        
        return result


# Funções de conveniência
def quick_evaluate_utility(model_func: Callable[[str], str]) -> float:
    """Avaliação rápida de utilidade"""
    evaluator = UtilityEvaluator()
    U_score, _ = evaluator.evaluate_all(model_func)
    return U_score


def quick_evaluate_stability(model_func: Callable[[str], str]) -> float:
    """Avaliação rápida de estabilidade"""
    evaluator = StabilityEvaluator()
    test_prompts = ["Teste 1", "Teste 2", "Teste 3"]
    S_score, _ = evaluator.evaluate_stability(model_func, test_prompts)
    return S_score


def quick_evaluate_cost(total_cost: float, tokens: int, latency: float) -> float:
    """Avaliação rápida de custo"""
    evaluator = CostEvaluator()
    C_score, _ = evaluator.evaluate_cost(total_cost, tokens, latency)
    return C_score


def quick_evaluate_learning(responses: List[str]) -> float:
    """Avaliação rápida de aprendizado"""
    evaluator = LearningEvaluator()
    L_score, _ = evaluator.evaluate_learning_potential(responses, {})
    return L_score


# Exemplo de uso
if __name__ == "__main__":
    print("📊 Demonstração: Evaluators - Suíte U/S/C/L")
    print("=" * 60)
    
    # Modelo mock para demonstração
    def mock_model(prompt: str) -> str:
        """Modelo mock que gera respostas determinísticas"""
        if "json" in prompt.lower():
            return '{"nome": "João Silva", "email": "joao@email.com", "telefone": "(11) 99999-9999"}'
        elif "capital" in prompt.lower():
            return "Brasília"
        elif "resumo" in prompt.lower():
            return "IA transforma economia com investimentos, mas gera preocupações."
        else:
            return f"Resposta para: {prompt[:30]}..."
            
    # Avaliação completa
    evaluator = ComprehensiveEvaluator(baseline_cost_usd=0.01)
    
    result = evaluator.evaluate_model(
        mock_model,
        config={"temperature": 0.7, "max_tokens": 1000},
        provider_id="mock-provider",
        model_name="mock-model"
    )
    
    print("✅ Avaliação completa:")
    print(f"   U (Utilidade): {result.U:.3f}")
    print(f"   S (Estabilidade): {result.S:.3f}")
    print(f"   C (Custo): {result.C:.3f}")
    print(f"   L (Aprendizado): {result.L:.3f}")
    print()
    
    print("📈 Métricas técnicas:")
    print(f"   Tokens: {result.total_tokens}")
    print(f"   Custo: ${result.total_cost_usd:.4f}")
    print(f"   Latência: {result.avg_latency_ms:.1f}ms")
    print(f"   Duração: {result.duration_s:.2f}s")
    print()
    
    print("🔍 Detalhes das tarefas:")
    for task_result in result.task_results:
        print(f"   {task_result.task_id}: {task_result.score:.3f} ({task_result.metric_name})")
        
    print("\n✅ Evaluators implementados e funcionando!")
    print("🔄 Próximo: Implementar ACFA (liga canário + promoção)")