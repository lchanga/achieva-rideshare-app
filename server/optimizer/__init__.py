"""
Optimizer package.

This package provides a single entrypoint:

  optimize_tours(request_json: dict) -> dict

The returned dict is shaped like Google's OptimizeToursResponse. The underlying
implementation is selected via OPTIMIZER_MODE (fake|google).
"""

from server.optimizer.factory import get_optimizer


def optimize_tours(request_json: dict) -> dict:
    return get_optimizer().optimize_tours(request_json)

