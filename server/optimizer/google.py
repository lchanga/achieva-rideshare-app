from __future__ import annotations

from server.optimizer.base import Optimizer


class GoogleOptimizer(Optimizer):
    """
    Placeholder for the real Google Route Optimization API implementation.

    This will eventually:
    - call POST https://routeoptimization.googleapis.com/v1/projects/{project}:optimizeTours
    - pass through the OptimizeToursRequest JSON
    - return the OptimizeToursResponse JSON
    """

    def optimize_tours(self, request_json: dict) -> dict:
        raise NotImplementedError("Google optimizer is not implemented yet")

