from __future__ import annotations

import os

from server.optimizer.base import BaseOptimizer
from server.optimizer.fake import FakeOptimizer
from server.optimizer.google import GoogleOptimizer


def get_optimizer() -> type[BaseOptimizer]:
    mode = os.getenv("OPTIMIZER_MODE", "fake").strip().lower()
    if mode == "google":
        return GoogleOptimizer
    return FakeOptimizer
