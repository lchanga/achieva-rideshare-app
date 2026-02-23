from __future__ import annotations

import os

from server.optimizer.base import Optimizer
from server.optimizer.fake import FakeOptimizer
from server.optimizer.google import GoogleOptimizer


def get_optimizer() -> Optimizer:
    """
    Pick an optimizer backend.

    - OPTIMIZER_MODE=fake   (default)
    - OPTIMIZER_MODE=google
    """
    mode = (os.getenv("OPTIMIZER_MODE") or "fake").strip().lower()
    return GoogleOptimizer() if mode == "google" else FakeOptimizer()

