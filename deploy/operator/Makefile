# PENIN-Ω Kubernetes Operator Makefile

# Variables
OPERATOR_IMAGE ?= ghcr.io/danielgonzagat/penin-operator
OPERATOR_TAG ?= latest
NAMESPACE ?= penin-system

.PHONY: help
help: ## Show this help message
	@echo "PENIN-Ω Kubernetes Operator"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

.PHONY: install-crds
install-crds: ## Install Custom Resource Definitions
	kubectl apply -f crds/peninaomegacluster-crd.yaml
	@echo "✓ CRDs installed"

.PHONY: install-operator
install-operator: ## Install the operator
	kubectl apply -f manifests/operator.yaml
	@echo "✓ Operator installed in namespace: $(NAMESPACE)"

.PHONY: install
install: install-crds install-operator ## Install CRDs and operator
	@echo "✓ Complete installation finished"
	@echo ""
	@echo "Verify with: kubectl get pods -n $(NAMESPACE)"

.PHONY: uninstall
uninstall: ## Uninstall operator and CRDs
	kubectl delete -f manifests/operator.yaml --ignore-not-found=true
	kubectl delete -f crds/peninaomegacluster-crd.yaml --ignore-not-found=true
	@echo "✓ Operator uninstalled"

.PHONY: build
build: ## Build operator Docker image
	docker build -t $(OPERATOR_IMAGE):$(OPERATOR_TAG) -f Dockerfile ../..
	@echo "✓ Image built: $(OPERATOR_IMAGE):$(OPERATOR_TAG)"

.PHONY: push
push: ## Push operator image to registry
	docker push $(OPERATOR_IMAGE):$(OPERATOR_TAG)
	@echo "✓ Image pushed: $(OPERATOR_IMAGE):$(OPERATOR_TAG)"

.PHONY: deploy-dev
deploy-dev: ## Deploy development cluster
	kubectl apply -f examples/cluster-dev.yaml
	@echo "✓ Development cluster deployed"
	@echo ""
	@echo "Check status with: kubectl get penin penin-dev"

.PHONY: deploy-prod
deploy-prod: ## Deploy production cluster
	kubectl create namespace penin-prod --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f examples/cluster-production.yaml
	@echo "✓ Production cluster deployed"
	@echo ""
	@echo "Check status with: kubectl get penin -n penin-prod"

.PHONY: delete-dev
delete-dev: ## Delete development cluster
	kubectl delete -f examples/cluster-dev.yaml --ignore-not-found=true
	@echo "✓ Development cluster deleted"

.PHONY: delete-prod
delete-prod: ## Delete production cluster
	kubectl delete -f examples/cluster-production.yaml --ignore-not-found=true
	@echo "✓ Production cluster deleted"

.PHONY: status
status: ## Show operator and cluster status
	@echo "Operator Status:"
	@kubectl get pods -n $(NAMESPACE) -l app=penin-omega,component=operator
	@echo ""
	@echo "Clusters:"
	@kubectl get penin --all-namespaces
	@echo ""
	@echo "All PENIN-Ω pods:"
	@kubectl get pods --all-namespaces -l app=penin-omega

.PHONY: logs
logs: ## Show operator logs
	kubectl logs -n $(NAMESPACE) -l app=penin-omega,component=operator -f

.PHONY: logs-dev
logs-dev: ## Show development cluster logs
	@echo "Ω-META logs:"
	@kubectl logs -l app=penin-omega,cluster=penin-dev,service=omega-meta --tail=20
	@echo ""
	@echo "Σ-Guard logs:"
	@kubectl logs -l app=penin-omega,cluster=penin-dev,service=sigma-guard --tail=20

.PHONY: test
test: ## Run operator tests
	pytest ../../tests/operator/ -v

.PHONY: validate
validate: ## Validate CRD and manifests
	kubectl apply --dry-run=client -f crds/peninaomegacluster-crd.yaml
	kubectl apply --dry-run=client -f manifests/operator.yaml
	kubectl apply --dry-run=client -f examples/cluster-dev.yaml
	@echo "✓ All manifests are valid"

.PHONY: clean
clean: ## Clean up local files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned up local files"

.PHONY: port-forward-dev
port-forward-dev: ## Port-forward to development cluster services
	@echo "Forwarding ports for penin-dev cluster..."
	@echo "Ω-META: http://localhost:8010"
	@echo "Σ-Guard: http://localhost:8011"
	@echo "SR-Ω∞: http://localhost:8012"
	@echo "ACFA League: http://localhost:8013"
	@echo ""
	kubectl port-forward -n default svc/penin-dev-omega-meta 8010:8010 &
	kubectl port-forward -n default svc/penin-dev-sigma-guard 8011:8011 &
	kubectl port-forward -n default svc/penin-dev-sr-omega-infinity 8012:8012 &
	kubectl port-forward -n default svc/penin-dev-acfa-league 8013:8013 &
	@echo "Press Ctrl+C to stop port forwarding"

.PHONY: describe-dev
describe-dev: ## Describe development cluster
	kubectl describe penin penin-dev

.PHONY: describe-operator
describe-operator: ## Describe operator deployment
	kubectl describe deployment -n $(NAMESPACE) penin-operator

.PHONY: restart-operator
restart-operator: ## Restart operator
	kubectl rollout restart deployment -n $(NAMESPACE) penin-operator
	@echo "✓ Operator restarted"

.PHONY: run-local
run-local: ## Run operator locally (for development)
	@echo "Running operator locally..."
	python penin_operator.py

.PHONY: dev-setup
dev-setup: ## Setup development environment
	pip install -r requirements.txt
	pip install pytest pytest-asyncio
	@echo "✓ Development environment ready"

.PHONY: all
all: install deploy-dev ## Install operator and deploy development cluster
