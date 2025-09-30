package penin.evolution

# Evolution and Mutation Policies
# Controls the auto-evolution process and mutation strategies

import rego.v1

# Default deny for evolution operations
default allow_evolution := false

# Allow evolution if all conditions are met
allow_evolution if {
    stability_gate_pass
    performance_gate_pass
    ethics_gate_pass
    resource_gate_pass
}

# Stability Gate: System must be stable before evolution
stability_gate_pass if {
    input.stability.uptime >= 3600  # 1 hour minimum uptime
    input.stability.error_rate <= 0.05  # 5% max error rate
    input.stability.consistency_score >= 0.8
}

# Performance Gate: Performance must be acceptable
performance_gate_pass if {
    input.performance.latency_p95 <= 2.0  # 95th percentile latency < 2s
    input.performance.throughput >= 100  # Min 100 requests/second
    input.performance.success_rate >= 0.95  # 95% success rate
}

# Ethics Gate: Ethics metrics must be within bounds
ethics_gate_pass if {
    input.ethics.ece <= 0.01
    input.ethics.bias_ratio <= 1.05
    input.ethics.fairness_score >= 0.8
}

# Resource Gate: Resources must be available
resource_gate_pass if {
    input.resources.cpu_usage < 0.8
    input.resources.memory_usage < 0.8
    input.resources.disk_usage < 0.9
}

# Mutation strategy selection
mutation_strategy := strategy if {
    strategy := select_strategy(input)
}

# Select mutation strategy based on current state
select_strategy(input) := "conservative" if {
    input.stability.consistency_score < 0.9
    input.performance.success_rate < 0.98
}

select_strategy(input) := "moderate" if {
    input.stability.consistency_score >= 0.9
    input.performance.success_rate >= 0.98
    input.performance.latency_p95 > 1.0
}

select_strategy(input) := "aggressive" if {
    input.stability.consistency_score >= 0.95
    input.performance.success_rate >= 0.99
    input.performance.latency_p95 <= 1.0
    input.resources.cpu_usage < 0.6
}

# Evolution parameters
evolution_parameters := {
    "mutation_rate": mutation_rate,
    "population_size": population_size,
    "generation_limit": generation_limit,
    "fitness_threshold": fitness_threshold
}

# Mutation rate based on strategy
mutation_rate := 0.01 if {
    select_strategy(input) == "conservative"
}

mutation_rate := 0.05 if {
    select_strategy(input) == "moderate"
}

mutation_rate := 0.1 if {
    select_strategy(input) == "aggressive"
}

# Population size based on resources
population_size := 10 if {
    input.resources.cpu_usage < 0.5
    input.resources.memory_usage < 0.5
}

population_size := 5 if {
    input.resources.cpu_usage >= 0.5
    input.resources.memory_usage >= 0.5
}

# Generation limit
generation_limit := 50 if {
    select_strategy(input) == "conservative"
}

generation_limit := 100 if {
    select_strategy(input) == "moderate"
}

generation_limit := 200 if {
    select_strategy(input) == "aggressive"
}

# Fitness threshold
fitness_threshold := 0.8 if {
    select_strategy(input) == "conservative"
}

fitness_threshold := 0.7 if {
    select_strategy(input) == "moderate"
}

fitness_threshold := 0.6 if {
    select_strategy(input) == "aggressive"
}

# Rollback conditions
rollback_required if {
    input.performance.error_rate > 0.1
    input.ethics.ece > 0.02
    input.resources.cpu_usage > 0.95
}

# Evolution monitoring
evolution_monitoring := {
    "fitness_trend": fitness_trend,
    "diversity_score": diversity_score,
    "convergence_rate": convergence_rate
}

# Fitness trend analysis
fitness_trend := "improving" if {
    input.fitness.current > input.fitness.previous
    input.fitness.current > input.fitness.baseline
}

fitness_trend := "stable" if {
    abs(input.fitness.current - input.fitness.previous) <= 0.01
}

fitness_trend := "declining" if {
    input.fitness.current < input.fitness.previous
    input.fitness.current < input.fitness.baseline
}

# Diversity score (higher is better)
diversity_score := score if {
    score := input.diversity.genetic_diversity
    score >= 0.5
}

# Convergence rate
convergence_rate := "fast" if {
    input.convergence.generations_to_convergence <= 20
}

convergence_rate := "moderate" if {
    input.convergence.generations_to_convergence > 20
    input.convergence.generations_to_convergence <= 50
}

convergence_rate := "slow" if {
    input.convergence.generations_to_convergence > 50
}