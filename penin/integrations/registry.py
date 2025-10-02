"""
Integration Registry for SOTA technologies.

Manages lifecycle and discovery of all external integrations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from penin.integrations.base import BaseIntegrationAdapter

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """
    Central registry for all SOTA integrations.

    Provides:
    - Dynamic loading of integrations
    - Status monitoring
    - Metrics aggregation
    - Fail-safe fallback
    """

    _instance: IntegrationRegistry | None = None
    _adapters: dict[str, BaseIntegrationAdapter] = {}

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._adapters = {}
        return cls._instance

    def register(self, name: str, adapter: BaseIntegrationAdapter) -> None:
        """
        Register a new integration adapter.

        Args:
            name: Unique name for the adapter
            adapter: Adapter instance
        """
        if name in self._adapters:
            logger.warning(f"Overwriting existing adapter: {name}")
        self._adapters[name] = adapter
        logger.info(f"Registered SOTA integration: {name}")

    def get(self, name: str) -> BaseIntegrationAdapter | None:
        """
        Get adapter by name.

        Args:
            name: Adapter name

        Returns:
            Adapter instance or None if not found
        """
        return self._adapters.get(name)

    def load(self, *names: str) -> dict[str, bool]:
        """
        Load and initialize multiple integrations.

        Args:
            *names: Integration names to load

        Returns:
            Dictionary mapping name to success status
        """
        results = {}
        for name in names:
            try:
                adapter = self._load_adapter(name)
                if adapter and adapter.initialize():
                    self.register(name, adapter)
                    results[name] = True
                    logger.info(f"Loaded SOTA integration: {name}")
                else:
                    results[name] = False
                    logger.warning(f"Failed to load integration: {name}")
            except Exception as e:
                results[name] = False
                logger.error(f"Error loading integration {name}: {e}")
        return results

    def _load_adapter(self, name: str) -> BaseIntegrationAdapter | None:
        """
        Dynamically load adapter by name.

        Args:
            name: Integration name (e.g., "nextpy", "metacog", "spikingjelly")

        Returns:
            Adapter instance or None
        """
        # Map short names to adapter paths
        adapter_map = {
            "nextpy": "penin.integrations.evolution.nextpy_ams.NextPyModifier",
            "metacog": "penin.integrations.metacognition.metacognitive_prompt.MetacognitiveReasoner",
            "spikingjelly": "penin.integrations.neuromorphic.spikingjelly_adapter.SpikingNetworkAdapter",
            "goneat": "penin.integrations.evolution.goneat_adapter.GoNEATAdapter",
            "mammoth": "penin.integrations.learning.mammoth_adapter.MammothAdapter",
            "symbolicai": "penin.integrations.symbolic.symbolicai_adapter.SymbolicAIAdapter",
            "midwiving": "penin.integrations.consciousness.midwiving_protocol.MidwivingProtocol",
            "opencog": "penin.integrations.agi.opencog_adapter.OpenCogAdapter",
            "swarmrl": "penin.integrations.swarm.swarmrl_adapter.SwarmRLAdapter",
        }

        adapter_path = adapter_map.get(name)
        if not adapter_path:
            logger.error(f"Unknown integration: {name}")
            return None

        try:
            module_path, class_name = adapter_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            adapter_class = getattr(module, class_name)
            return adapter_class()
        except (ImportError, AttributeError) as e:
            logger.warning(f"Adapter {name} not yet implemented: {e}")
            return None

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """
        Get status of all registered integrations.

        Returns:
            Dictionary mapping adapter name to status dict
        """
        return {name: adapter.get_status() for name, adapter in self._adapters.items()}

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """
        Get metrics from all registered integrations.

        Returns:
            Dictionary mapping adapter name to metrics dict
        """
        return {name: adapter.get_metrics() for name, adapter in self._adapters.items()}

    def list_available(self) -> list[str]:
        """
        List all available (installed) integrations.

        Returns:
            List of integration names
        """
        return [
            name for name, adapter in self._adapters.items() if adapter.is_available()
        ]

    def list_active(self) -> list[str]:
        """
        List all currently active integrations.

        Returns:
            List of integration names
        """
        from penin.integrations.base import IntegrationStatus

        return [
            name
            for name, adapter in self._adapters.items()
            if adapter.status
            in (IntegrationStatus.ACTIVE, IntegrationStatus.INITIALIZED)
        ]

    def unregister(self, name: str) -> bool:
        """
        Unregister an integration.

        Args:
            name: Adapter name

        Returns:
            True if unregistered, False if not found
        """
        if name in self._adapters:
            del self._adapters[name]
            logger.info(f"Unregistered integration: {name}")
            return True
        return False

    def clear(self) -> None:
        """Clear all registrations"""
        self._adapters.clear()
        logger.info("Cleared all integrations")


# Singleton instance
_registry = IntegrationRegistry()


def get_registry() -> IntegrationRegistry:
    """Get the global integration registry"""
    return _registry


__all__ = ["IntegrationRegistry", "get_registry"]
