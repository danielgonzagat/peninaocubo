"""
Tests for the PENIN-Ω Kubernetes Operator

These tests validate the operator's core functionality including:
- Manifest generation
- Service configuration
- Resource management
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

# Mock kopf and kubernetes modules before importing operator
sys.modules['kopf'] = MagicMock()
sys.modules['kubernetes'] = MagicMock()
sys.modules['kubernetes.client'] = MagicMock()
sys.modules['kubernetes.config'] = MagicMock()

# Add operator directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../deploy/operator"))

from penin_operator import (
    SERVICES,
    create_deployment_manifest,
    create_redis_manifest,
    create_service_manifest,
)


@pytest.fixture
def basic_spec():
    """Basic cluster specification for testing."""
    return {
        "version": "0.9.0",
        "replicas": {
            "omegaMeta": 1,
            "sigmaGuard": 2,
            "srOmegaInfinity": 1,
            "acfaLeague": 1,
        },
        "resources": {
            "omegaMeta": {"cpu": "500m", "memory": "512Mi"},
            "sigmaGuard": {"cpu": "250m", "memory": "256Mi"},
        },
        "config": {
            "budgetDailyUsd": 5.0,
            "caosPlus": {"maxBoost": 0.05, "kappa": 20.0},
            "sigmaGuard": {"eceThreshold": 0.01, "biasThreshold": 1.05},
            "evolution": {"seed": 12345},
        },
        "storage": {
            "cache": {"enabled": True, "type": "redis"},
        },
    }


@pytest.fixture
def owner_references():
    """Sample owner references for testing."""
    return [
        {
            "apiVersion": "penin.ai/v1alpha1",
            "kind": "PeninOmegaCluster",
            "name": "test-cluster",
            "uid": "12345",
            "controller": True,
            "blockOwnerDeletion": True,
        }
    ]


def test_services_definition():
    """Test that all required services are defined."""
    assert "omega-meta" in SERVICES
    assert "sigma-guard" in SERVICES
    assert "sr-omega-infinity" in SERVICES
    assert "acfa-league" in SERVICES

    # Verify each service has required fields
    for _service_name, config in SERVICES.items():
        assert "port" in config
        assert "command" in config
        assert isinstance(config["port"], int)
        assert isinstance(config["command"], list)


def test_create_service_manifest(basic_spec, owner_references):
    """Test Service manifest creation."""
    service_name = "omega-meta"
    service_config = SERVICES[service_name]

    manifest = create_service_manifest(
        name="test-cluster",
        namespace="default",
        service_name=service_name,
        service_config=service_config,
        spec=basic_spec,
        owner_references=owner_references,
    )

    # Verify basic structure
    assert manifest["apiVersion"] == "v1"
    assert manifest["kind"] == "Service"
    assert manifest["metadata"]["name"] == "test-cluster-omega-meta"
    assert manifest["metadata"]["namespace"] == "default"

    # Verify labels
    labels = manifest["metadata"]["labels"]
    assert labels["app"] == "penin-omega"
    assert labels["cluster"] == "test-cluster"
    assert labels["service"] == service_name

    # Verify owner references
    assert manifest["metadata"]["ownerReferences"] == owner_references

    # Verify spec
    assert manifest["spec"]["type"] == "ClusterIP"
    assert manifest["spec"]["ports"][0]["port"] == service_config["port"]
    assert manifest["spec"]["selector"]["service"] == service_name


def test_create_deployment_manifest(basic_spec, owner_references):
    """Test Deployment manifest creation."""
    service_name = "omega-meta"
    service_config = SERVICES[service_name]

    manifest = create_deployment_manifest(
        name="test-cluster",
        namespace="default",
        service_name=service_name,
        service_config=service_config,
        spec=basic_spec,
        owner_references=owner_references,
    )

    # Verify basic structure
    assert manifest["apiVersion"] == "apps/v1"
    assert manifest["kind"] == "Deployment"
    assert manifest["metadata"]["name"] == "test-cluster-omega-meta"

    # Verify replica count
    assert manifest["spec"]["replicas"] == 1

    # Verify container configuration
    container = manifest["spec"]["template"]["spec"]["containers"][0]
    assert container["name"] == service_name
    assert container["image"] == "ghcr.io/danielgonzagat/peninaocubo:0.9.0"
    assert container["command"] == service_config["command"]

    # Verify resources
    assert container["resources"]["requests"]["cpu"] == "500m"
    assert container["resources"]["requests"]["memory"] == "512Mi"

    # Verify environment variables
    env_vars = {env["name"]: env["value"] for env in container["env"]}
    assert "PENIN_BUDGET_DAILY_USD" in env_vars
    assert env_vars["PENIN_BUDGET_DAILY_USD"] == "5.0"
    assert env_vars["PENIN_CAOS_PLUS__KAPPA"] == "20.0"

    # Verify probes
    assert "livenessProbe" in container
    assert "readinessProbe" in container
    assert container["livenessProbe"]["httpGet"]["path"] == "/health"
    assert container["livenessProbe"]["httpGet"]["port"] == service_config["port"]


def test_deployment_with_custom_replicas(basic_spec, owner_references):
    """Test deployment with custom replica count."""
    service_name = "sigma-guard"
    service_config = SERVICES[service_name]

    manifest = create_deployment_manifest(
        name="test-cluster",
        namespace="default",
        service_name=service_name,
        service_config=service_config,
        spec=basic_spec,
        owner_references=owner_references,
    )

    # Verify replica count matches spec
    assert manifest["spec"]["replicas"] == 2


def test_deployment_with_custom_resources(basic_spec, owner_references):
    """Test deployment with custom resource limits."""
    service_name = "sigma-guard"
    service_config = SERVICES[service_name]

    manifest = create_deployment_manifest(
        name="test-cluster",
        namespace="default",
        service_name=service_name,
        service_config=service_config,
        spec=basic_spec,
        owner_references=owner_references,
    )

    container = manifest["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"]["requests"]["cpu"] == "250m"
    assert container["resources"]["requests"]["memory"] == "256Mi"


def test_create_redis_manifest(owner_references):
    """Test Redis deployment and service creation."""
    deployment, service = create_redis_manifest(
        name="test-cluster",
        namespace="default",
        owner_references=owner_references,
    )

    # Verify deployment
    assert deployment["kind"] == "Deployment"
    assert deployment["metadata"]["name"] == "test-cluster-redis"
    assert deployment["spec"]["replicas"] == 1

    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert container["image"] == "redis:7-alpine"
    assert container["ports"][0]["containerPort"] == 6379

    # Verify service
    assert service["kind"] == "Service"
    assert service["metadata"]["name"] == "test-cluster-redis"
    assert service["spec"]["ports"][0]["port"] == 6379


def test_deployment_prometheus_annotations(basic_spec, owner_references):
    """Test that Prometheus annotations are added correctly."""
    service_name = "omega-meta"
    service_config = SERVICES[service_name]

    manifest = create_deployment_manifest(
        name="test-cluster",
        namespace="default",
        service_name=service_name,
        service_config=service_config,
        spec=basic_spec,
        owner_references=owner_references,
    )

    annotations = manifest["spec"]["template"]["metadata"]["annotations"]
    assert annotations["prometheus.io/scrape"] == "true"
    assert annotations["prometheus.io/port"] == str(service_config["port"])
    assert annotations["prometheus.io/path"] == "/metrics"


def test_deployment_labels(basic_spec, owner_references):
    """Test that labels are correctly applied."""
    service_name = "omega-meta"
    service_config = SERVICES[service_name]

    manifest = create_deployment_manifest(
        name="test-cluster",
        namespace="default",
        service_name=service_name,
        service_config=service_config,
        spec=basic_spec,
        owner_references=owner_references,
    )

    # Check deployment labels
    labels = manifest["metadata"]["labels"]
    assert labels["app"] == "penin-omega"
    assert labels["cluster"] == "test-cluster"
    assert labels["service"] == service_name

    # Check pod labels
    pod_labels = manifest["spec"]["template"]["metadata"]["labels"]
    assert pod_labels == labels


def test_default_values(owner_references):
    """Test that default values are used when not specified."""
    minimal_spec = {"version": "0.9.0"}

    manifest = create_deployment_manifest(
        name="test-cluster",
        namespace="default",
        service_name="omega-meta",
        service_config=SERVICES["omega-meta"],
        spec=minimal_spec,
        owner_references=owner_references,
    )

    # Should use default replica count
    assert manifest["spec"]["replicas"] == 1

    # Should use default resources
    container = manifest["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"]["requests"]["cpu"] == "500m"

    # Should have default environment variables
    env_vars = {env["name"]: env["value"] for env in container["env"]}
    assert env_vars["PENIN_BUDGET_DAILY_USD"] == "5.0"


def test_environment_variable_configuration(basic_spec, owner_references):
    """Test that all configuration options are properly converted to env vars."""
    service_name = "sigma-guard"
    service_config = SERVICES[service_name]

    manifest = create_deployment_manifest(
        name="test-cluster",
        namespace="default",
        service_name=service_name,
        service_config=service_config,
        spec=basic_spec,
        owner_references=owner_references,
    )

    container = manifest["spec"]["template"]["spec"]["containers"][0]
    env_vars = {env["name"]: env["value"] for env in container["env"]}

    # Verify all config sections are present
    assert env_vars["PENIN_BUDGET_DAILY_USD"] == "5.0"
    assert env_vars["PENIN_CAOS_PLUS__MAX_BOOST"] == "0.05"
    assert env_vars["PENIN_CAOS_PLUS__KAPPA"] == "20.0"
    assert env_vars["PENIN_SIGMA_GUARD__ECE_THRESHOLD"] == "0.01"
    assert env_vars["PENIN_SIGMA_GUARD__BIAS_THRESHOLD"] == "1.05"
    assert env_vars["PENIN_EVOLUTION__SEED"] == "12345"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
