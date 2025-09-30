package penin.budget

# Budget and Cost Control Policies
# Implements cost-aware routing and budget enforcement

import rego.v1

# Default deny for budget operations
default allow_budget_operation := false

# Allow budget operation if within limits
allow_budget_operation if {
    within_daily_budget
    within_hourly_budget
    within_request_limit
}

# Check daily budget
within_daily_budget if {
    input.budget.daily_spend < input.budget.daily_limit
    input.budget.daily_spend + input.request.cost <= input.budget.daily_limit
}

# Check hourly budget (1/24 of daily budget)
within_hourly_budget if {
    hourly_limit := input.budget.daily_limit / 24
    input.budget.hourly_spend < hourly_limit
    input.budget.hourly_spend + input.request.cost <= hourly_limit
}

# Check request limit (max cost per request)
within_request_limit if {
    input.request.cost <= input.budget.max_request_cost
}

# Provider selection based on cost and quality
select_provider(input) := provider if {
    provider := input.providers[_]
    provider.cost <= input.budget.max_request_cost
    provider.quality_score >= input.budget.min_quality_threshold
    provider.available == true
}

# Cost optimization recommendations
cost_optimization := {
    "recommended_provider": recommend_provider(input),
    "cost_savings": calculate_savings(input),
    "quality_tradeoff": assess_quality_tradeoff(input)
}

# Recommend provider based on cost/quality ratio
recommend_provider(input) := provider if {
    provider := input.providers[_]
    cost_quality_ratio := provider.cost / provider.quality_score
    cost_quality_ratio == min([p.cost / p.quality_score | p := input.providers[_]; p.available == true])
}

# Calculate potential savings
calculate_savings(input) := savings if {
    current_provider := input.current_provider
    recommended_provider := recommend_provider(input)
    savings := current_provider.cost - recommended_provider.cost
}

# Assess quality tradeoff
assess_quality_tradeoff(input) := "acceptable" if {
    recommended_provider := recommend_provider(input)
    quality_drop := input.current_provider.quality_score - recommended_provider.quality_score
    quality_drop <= 0.1
}

assess_quality_tradeoff(input) := "significant" if {
    recommended_provider := recommend_provider(input)
    quality_drop := input.current_provider.quality_score - recommended_provider.quality_score
    quality_drop > 0.1
}

# Budget alerts
budget_alerts := {
    "daily_warning": daily_budget_warning,
    "hourly_warning": hourly_budget_warning,
    "request_warning": request_cost_warning
}

# Daily budget warning (80% threshold)
daily_budget_warning if {
    input.budget.daily_spend >= input.budget.daily_limit * 0.8
}

# Hourly budget warning (80% threshold)
hourly_budget_warning if {
    hourly_limit := input.budget.daily_limit / 24
    input.budget.hourly_spend >= hourly_limit * 0.8
}

# Request cost warning (exceeds average)
request_cost_warning if {
    input.request.cost > input.budget.avg_request_cost * 1.5
}