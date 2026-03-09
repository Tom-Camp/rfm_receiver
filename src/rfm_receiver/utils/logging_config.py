from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def configure_logging(log_dir: str | Path = "logs") -> None:
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()  # remove the default stderr handler [web:12]

    # Console (optional)
    logger.add(sys.stderr, level="INFO")

    # General app log (everything at INFO and above)
    logger.add(
        log_dir / "app.log",
        level="INFO",
        rotation="10 MB",
        retention="14 days",
        enqueue=True,
    )  # rotation/retention are supported for file sinks [web:1]

    # Error log (ERROR and above only)
    logger.add(
        log_dir / "error.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )  # backtrace/diagnose are logger.add() options [web:8]
