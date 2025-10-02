# PENIN-Ω Multi-LLM Router Policy
# ==================================
#
# Budget control, circuit breakers, and routing decisions.

package penin.router

import rego.v1

# Default deny
default allow_request := false
default route_decision := "block"

# ============================================================================
# BUDGET CONTROL
# ============================================================================

# Check if budget allows request
budget_available if {
    input.budget.daily_usd_max > 0
    input.budget.used_usd < input.budget.daily_usd_max
}

budget_soft_warning if {
    input.budget.used_pct >= 0.95
    input.budget.used_pct < 1.00
}

budget_hard_stop if {
    input.budget.used_pct >= 1.00
}

# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

circuit_closed if {
    input.provider.consecutive_failures < 3
}

circuit_open if {
    input.provider.consecutive_failures >= 3
}

circuit_half_open if {
    circuit_open
    time.now_ns() - input.provider.last_failure_ns > 60000000000  # 60s in ns
}

# Provider is available
provider_available if {
    circuit_closed
}

provider_available if {
    circuit_half_open
    input.provider.half_open_calls < 1
}

# ============================================================================
# COST OPTIMIZATION
# ============================================================================

# Select cheapest provider from available
cheapest_provider := provider if {
    available := [p | 
        some p in input.providers
        p.status == "healthy"
        p.cost_per_token < input.budget.remaining_budget
    ]
    count(available) > 0
    provider := min_by(available, "cost_per_token")
}

# Select provider by performance
best_provider := provider if {
    available := [p | 
        some p in input.providers
        p.status == "healthy"
        p.success_rate >= 0.95
    ]
    count(available) > 0
    provider := min_by(available, "avg_latency_ms")
}

# ============================================================================
# ROUTING DECISION
# ============================================================================

route_decision := "allow" if {
    budget_available
    not budget_hard_stop
    provider_available
}

route_decision := "block_budget" if {
    budget_hard_stop
}

route_decision := "block_circuit" if {
    circuit_open
    not circuit_half_open
}

route_decision := "warn_budget" if {
    budget_soft_warning
    provider_available
}

allow_request if {
    route_decision == "allow"
}

allow_request if {
    route_decision == "warn_budget"
}

# ============================================================================
# FALLBACK ROUTING
# ============================================================================

# Enable fallback if primary fails
enable_fallback if {
    input.primary_provider.status != "healthy"
    count(input.fallback_providers) > 0
}

# Select fallback provider
fallback_provider := provider if {
    enable_fallback
    available := [p | 
        some p in input.fallback_providers
        p.status == "healthy"
    ]
    count(available) > 0
    provider := available[0]  # First available
}

# ============================================================================
# ANALYTICS
# ============================================================================

# Track metrics
should_track_metrics if {
    input.config.analytics.enabled == true
}

# Alert on high cost
cost_alert if {
    input.request.estimated_cost_usd > 1.0
}

# Alert on high latency
latency_alert if {
    input.provider.avg_latency_ms > 2000
}

# ============================================================================
# VERDICT
# ============================================================================

verdict := {
    "allow": allow_request,
    "decision": route_decision,
    "provider": cheapest_provider,
    "fallback": fallback_provider,
    "budget_status": {
        "available": budget_available,
        "warning": budget_soft_warning,
        "hard_stop": budget_hard_stop,
    },
    "circuit_status": {
        "closed": circuit_closed,
        "open": circuit_open,
        "half_open": circuit_half_open,
    },
    "alerts": {
        "cost": cost_alert,
        "latency": latency_alert,
    },
}
