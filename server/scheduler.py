from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from server.optimizer import get_optimizer

_scheduler_lock = threading.Lock()
_scheduler_started = False


def _run_scheduler_loop() -> None:
    timezone = ZoneInfo("America/New_York")
    scheduled_hour = int(os.getenv("NIGHTLY_OPTIMIZER_HOUR", "20"))
    scheduled_minute = int(os.getenv("NIGHTLY_OPTIMIZER_MINUTE", "5"))
    last_run_date = None

    while True:
        now = datetime.now(timezone)
        should_run = (
            now.hour == scheduled_hour
            and now.minute >= scheduled_minute
            and last_run_date != now.date()
        )
        if should_run:
            try:
                get_optimizer().run_optimization_sync()
            except Exception as exc:
                print(f"Nightly optimizer failed: {exc}")
            last_run_date = now.date()
        time.sleep(30)


def start_nightly_optimizer() -> None:
    global _scheduler_started

    if os.getenv("ENABLE_NIGHTLY_OPTIMIZER", "1") != "1":
        return

    # Avoid duplicate threads under the Flask debug reloader.
    if (
        os.getenv("FLASK_DEBUG", "0") == "1"
        and os.getenv("WERKZEUG_RUN_MAIN") not in {"true"}
    ):
        return

    with _scheduler_lock:
        if _scheduler_started:
            return
        thread = threading.Thread(
            target=_run_scheduler_loop,
            name="nightly-optimizer",
            daemon=True,
        )
        thread.start()
        _scheduler_started = True
