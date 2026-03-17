from __future__ import annotations

from abc import ABC, abstractmethod


class BaseOptimizer(ABC):
    @staticmethod
    @abstractmethod
    def run_optimization_sync() -> dict:
        """Generate and persist routes for the current optimization mode."""
