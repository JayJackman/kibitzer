"""Centralised logging setup for the bridge application.

Call ``setup_logging`` once at application startup (API lifespan or CLI
entry point) to configure the ``bridge.*`` logger hierarchy.
"""

import logging


def setup_logging(level: str = "INFO") -> None:
    """Configure the root and ``bridge`` loggers.

    Parameters
    ----------
    level:
        Logging level name (e.g. ``"INFO"``, ``"DEBUG"``).  Applied to the
        ``bridge`` logger so all sub-loggers inherit it.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
        level=numeric_level,
    )

    # Ensure the bridge logger hierarchy respects the requested level.
    logging.getLogger("bridge").setLevel(numeric_level)

    # Suppress uvicorn's per-request access log — our middleware handles it.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
