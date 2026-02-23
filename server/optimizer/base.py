from __future__ import annotations

from typing import Protocol


class Optimizer(Protocol):
    """
    Optimizer interface.

    Implementations must accept an OptimizeToursRequest JSON dict and return an
    OptimizeToursResponse JSON dict (Google Route Optimization API shape).
    """

    def optimize_tours(self, request_json: dict) -> dict: ...

