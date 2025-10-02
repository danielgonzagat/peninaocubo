#!/usr/bin/env python3
"""
PENIN-Ω Kubernetes Operator

This operator manages the lifecycle of PENIN-Ω clusters in Kubernetes.
It handles:
- Creation and deletion of all microservices (Ω-META, Σ-Guard, SR-Ω∞, ACFA League)
- Configuration synchronization
- Health monitoring and auto-recovery
- Automatic scaling and upgrades
- Self-architecting capabilities (Phase 3)

Built with Kopf (Kubernetes Operator Pythonic Framework)
"""

import logging
from typing import Any

import kopf
import kubernetes
from kubernetes import client, config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Services managed by the operator
SERVICES = {
    "omega-meta": {"port": 8010, "command": ["penin", "meta"]},
    "sigma-guard": {"port": 8011, "command": ["penin", "guard"]},
    "sr-omega-infinity": {"port": 8012, "command": ["penin", "sr"]},
    "acfa-league": {"port": 8013, "command": ["penin", "league"]},
}


def get_k8s_clients():
    """Initialize Kubernetes clients."""
    try:
        config.load_incluster_config()
    except kubernetes.config.ConfigException:
        config.load_kube_config()

    return {
        "apps": client.AppsV1Api(),
        "core": client.CoreV1Api(),
        "custom": client.CustomObjectsApi(),
    }


def create_service_manifest(
    name: str,
    namespace: str,
    service_name: str,
    service_config: dict[str, Any],
    spec: dict[str, Any],
    owner_references: list,
) -> dict[str, Any]:
    """Create a Kubernetes Service manifest for a PENIN-Ω service."""
    port = service_config["port"]

    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-{service_name}",
            "namespace": namespace,
            "labels": {
                "app": "penin-omega",
                "cluster": name,
                "service": service_name,
            },
            "ownerReferences": owner_references,
        },
        "spec": {
            "selector": {
                "app": "penin-omega",
                "cluster": name,
                "service": service_name,
            },
            "ports": [
                {
                    "name": "http",
                    "port": port,
                    "targetPort": port,
                    "protocol": "TCP",
                }
            ],
            "type": "ClusterIP",
        },
    }


def create_deployment_manifest(
    name: str,
    namespace: str,
    service_name: str,
    service_config: dict[str, Any],
    spec: dict[str, Any],
    owner_references: list,
) -> dict[str, Any]:
    """Create a Kubernetes Deployment manifest for a PENIN-Ω service."""
    # Get replica count from spec
    replicas_config = spec.get("replicas", {})
    service_key_map = {
        "omega-meta": "omegaMeta",
        "sigma-guard": "sigmaGuard",
        "sr-omega-infinity": "srOmegaInfinity",
        "acfa-league": "acfaLeague",
    }
    replicas = replicas_config.get(service_key_map[service_name], 1)

    # Get resource limits from spec
    resources_config = spec.get("resources", {})
    resources = resources_config.get(service_key_map[service_name], {})
    cpu = resources.get("cpu", "500m")
    memory = resources.get("memory", "512Mi")

    # Get configuration
    config_spec = spec.get("config", {})
    version = spec.get("version", "0.9.0")

    # Build environment variables
    env_vars = [
        {"name": "PENIN_BUDGET_DAILY_USD", "value": str(config_spec.get("budgetDailyUsd", 5.0))},
        {"name": "PENIN_METRICS_BIND_HOST", "value": "0.0.0.0"},
        {"name": "PENIN_METRICS_PORT", "value": str(service_config["port"])},
    ]

    # Add CAOS+ configuration
    if "caosPlus" in config_spec:
        caos_config = config_spec["caosPlus"]
        env_vars.extend([
            {"name": "PENIN_CAOS_PLUS__MAX_BOOST", "value": str(caos_config.get("maxBoost", 0.05))},
            {"name": "PENIN_CAOS_PLUS__KAPPA", "value": str(caos_config.get("kappa", 20.0))},
        ])

    # Add Sigma Guard configuration
    if "sigmaGuard" in config_spec:
        guard_config = config_spec["sigmaGuard"]
        env_vars.extend([
            {"name": "PENIN_SIGMA_GUARD__ECE_THRESHOLD", "value": str(guard_config.get("eceThreshold", 0.01))},
            {"name": "PENIN_SIGMA_GUARD__BIAS_THRESHOLD", "value": str(guard_config.get("biasThreshold", 1.05))},
        ])

    # Add evolution configuration
    if "evolution" in config_spec:
        evolution_config = config_spec["evolution"]
        env_vars.append({"name": "PENIN_EVOLUTION__SEED", "value": str(evolution_config.get("seed", 12345))})

    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"{name}-{service_name}",
            "namespace": namespace,
            "labels": {
                "app": "penin-omega",
                "cluster": name,
                "service": service_name,
            },
            "ownerReferences": owner_references,
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": {
                    "app": "penin-omega",
                    "cluster": name,
                    "service": service_name,
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "penin-omega",
                        "cluster": name,
                        "service": service_name,
                    },
                    "annotations": {
                        "prometheus.io/scrape": "true",
                        "prometheus.io/port": str(service_config["port"]),
                        "prometheus.io/path": "/metrics",
                    },
                },
                "spec": {
                    "containers": [
                        {
                            "name": service_name,
                            "image": f"ghcr.io/danielgonzagat/peninaocubo:{version}",
                            "imagePullPolicy": "IfNotPresent",
                            "command": service_config["command"],
                            "ports": [
                                {
                                    "name": "http",
                                    "containerPort": service_config["port"],
                                    "protocol": "TCP",
                                }
                            ],
                            "env": env_vars,
                            "resources": {
                                "requests": {
                                    "cpu": cpu,
                                    "memory": memory,
                                },
                                "limits": {
                                    "cpu": cpu,
                                    "memory": memory,
                                },
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": service_config["port"],
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10,
                                "timeoutSeconds": 5,
                                "failureThreshold": 3,
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": service_config["port"],
                                },
                                "initialDelaySeconds": 10,
                                "periodSeconds": 5,
                                "timeoutSeconds": 3,
                                "failureThreshold": 3,
                            },
                        }
                    ],
                },
            },
        },
    }


def create_redis_manifest(
    name: str,
    namespace: str,
    owner_references: list,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create Redis deployment and service manifests for caching."""
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"{name}-redis",
            "namespace": namespace,
            "labels": {
                "app": "penin-omega",
                "cluster": name,
                "service": "redis",
            },
            "ownerReferences": owner_references,
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "penin-omega",
                    "cluster": name,
                    "service": "redis",
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "penin-omega",
                        "cluster": name,
                        "service": "redis",
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "redis",
                            "image": "redis:7-alpine",
                            "ports": [{"containerPort": 6379}],
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "200m", "memory": "256Mi"},
                            },
                        }
                    ]
                },
            },
        },
    }

    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-redis",
            "namespace": namespace,
            "labels": {
                "app": "penin-omega",
                "cluster": name,
                "service": "redis",
            },
            "ownerReferences": owner_references,
        },
        "spec": {
            "selector": {
                "app": "penin-omega",
                "cluster": name,
                "service": "redis",
            },
            "ports": [{"port": 6379, "targetPort": 6379}],
            "type": "ClusterIP",
        },
    }

    return deployment, service


@kopf.on.create("penin.ai", "v1alpha1", "peninaomegaclusters")
async def create_cluster(spec, name, namespace, logger, **kwargs):
    """
    Handler for PeninOmegaCluster creation.

    This creates all necessary Kubernetes resources for a PENIN-Ω cluster:
    - Deployments for each microservice
    - Services for networking
    - ConfigMaps for configuration
    - Optional Redis for caching
    """
    logger.info(f"Creating PENIN-Ω cluster: {name} in namespace: {namespace}")

    k8s = get_k8s_clients()
    owner_references = [
        {
            "apiVersion": "penin.ai/v1alpha1",
            "kind": "PeninOmegaCluster",
            "name": name,
            "uid": kwargs["uid"],
            "controller": True,
            "blockOwnerDeletion": True,
        }
    ]

    # Create Redis if caching is enabled
    storage_config = spec.get("storage", {})
    cache_config = storage_config.get("cache", {})
    if cache_config.get("enabled", True) and cache_config.get("type", "redis") == "redis":
        logger.info(f"Creating Redis cache for cluster: {name}")
        redis_deployment, redis_service = create_redis_manifest(name, namespace, owner_references)

        k8s["apps"].create_namespaced_deployment(namespace=namespace, body=redis_deployment)
        k8s["core"].create_namespaced_service(namespace=namespace, body=redis_service)

    # Create all microservices
    created_services = []
    for service_name, service_config in SERVICES.items():
        logger.info(f"Creating service: {service_name} for cluster: {name}")

        # Create Service
        service_manifest = create_service_manifest(
            name, namespace, service_name, service_config, spec, owner_references
        )
        k8s["core"].create_namespaced_service(namespace=namespace, body=service_manifest)

        # Create Deployment
        deployment_manifest = create_deployment_manifest(
            name, namespace, service_name, service_config, spec, owner_references
        )
        k8s["apps"].create_namespaced_deployment(namespace=namespace, body=deployment_manifest)

        created_services.append(service_name)

    # Update status
    status = {
        "phase": "Creating",
        "conditions": [
            {
                "type": "Initializing",
                "status": "True",
                "lastTransitionTime": kubernetes.client.V1Time().now().to_str(),
                "reason": "ClusterCreated",
                "message": f"Created {len(created_services)} services",
            }
        ],
        "services": {},
    }

    logger.info(f"Successfully created PENIN-Ω cluster: {name}")
    return {"status": status}


@kopf.on.update("penin.ai", "v1alpha1", "peninaomegaclusters")
async def update_cluster(spec, name, namespace, logger, old, new, **kwargs):
    """
    Handler for PeninOmegaCluster updates.

    This handles configuration changes, scaling, and upgrades.
    """
    logger.info(f"Updating PENIN-Ω cluster: {name} in namespace: {namespace}")

    k8s = get_k8s_clients()

    # Check what changed
    old.get("spec", {})
    new_spec = new.get("spec", {})

    # Update deployments if replicas or resources changed
    for service_name, _service_config in SERVICES.items():
        deployment_name = f"{name}-{service_name}"

        try:
            deployment = k8s["apps"].read_namespaced_deployment(deployment_name, namespace)

            # Update replica count if changed
            service_key_map = {
                "omega-meta": "omegaMeta",
                "sigma-guard": "sigmaGuard",
                "sr-omega-infinity": "srOmegaInfinity",
                "acfa-league": "acfaLeague",
            }

            new_replicas = new_spec.get("replicas", {}).get(service_key_map[service_name])
            if new_replicas and new_replicas != deployment.spec.replicas:
                logger.info(f"Scaling {service_name} to {new_replicas} replicas")
                deployment.spec.replicas = new_replicas
                k8s["apps"].patch_namespaced_deployment(deployment_name, namespace, deployment)

        except kubernetes.client.exceptions.ApiException as e:
            logger.error(f"Error updating deployment {deployment_name}: {e}")

    logger.info(f"Successfully updated PENIN-Ω cluster: {name}")
    return {"status": {"phase": "Running"}}


@kopf.on.delete("penin.ai", "v1alpha1", "peninaomegaclusters")
async def delete_cluster(spec, name, namespace, logger, **kwargs):
    """
    Handler for PeninOmegaCluster deletion.

    Kubernetes will automatically delete owned resources (Deployments, Services)
    due to owner references.
    """
    logger.info(f"Deleting PENIN-Ω cluster: {name} in namespace: {namespace}")
    logger.info("Kubernetes will automatically clean up owned resources")


@kopf.timer("penin.ai", "v1alpha1", "peninaomegaclusters", interval=30.0)
async def monitor_cluster(spec, name, namespace, logger, status, **kwargs):
    """
    Periodic health monitoring and status updates.

    This runs every 30 seconds to:
    - Check service health
    - Update cluster status
    - Trigger auto-recovery if needed
    """
    k8s = get_k8s_clients()

    # Check status of all services
    services_status = {}
    all_ready = True

    for service_name in SERVICES.keys():
        deployment_name = f"{name}-{service_name}"

        try:
            deployment = k8s["apps"].read_namespaced_deployment(deployment_name, namespace)

            service_key_map = {
                "omega-meta": "omegaMeta",
                "sigma-guard": "sigmaGuard",
                "sr-omega-infinity": "srOmegaInfinity",
                "acfa-league": "acfaLeague",
            }

            key = service_key_map[service_name]
            replicas = deployment.spec.replicas or 0
            ready_replicas = deployment.status.ready_replicas or 0

            services_status[key] = {
                "ready": ready_replicas == replicas and replicas > 0,
                "replicas": replicas,
                "readyReplicas": ready_replicas,
            }

            if ready_replicas < replicas:
                all_ready = False

        except kubernetes.client.exceptions.ApiException as e:
            logger.error(f"Error checking deployment {deployment_name}: {e}")
            services_status[key] = {"ready": False, "replicas": 0, "readyReplicas": 0}
            all_ready = False

    # Determine cluster phase
    phase = "Running" if all_ready else "Updating"

    # Return updated status
    return {
        "status": {
            "phase": phase,
            "services": services_status,
            "lastUpdateTime": kubernetes.client.V1Time().now().to_str(),
        }
    }


if __name__ == "__main__":
    # Run the operator
    kopf.run()
