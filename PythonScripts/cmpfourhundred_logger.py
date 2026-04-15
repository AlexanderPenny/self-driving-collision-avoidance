"""
Log format:
    TIMESTAMP|EVENT_TYPE|DETAIL

Event types:
    SESSION_START       simulation launched
    SESSION_END         simulation closed
    CRASH               collision detected  (detail = object hit)
    RESET               env.reset() called
    TELEPORT            vehicle stuck, teleported to waypoint
    WAYPOINT_HIT        agent reached a path waypoint  (detail = waypoint index)
    INTERVENTION_START  AI takes over from human
    INTERVENTION_END    AI hands control back to human
    MODE_CHANGE         driving mode toggled  (detail = new mode name)
"""

import logging
import os
from datetime import datetime

LOG_FILE = "cmpfourhundred_session.log" # expected log file name
_LOGGER_NAME = "cmp400"

def _build_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:          # already set up (e.g. imported twice)
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False     # don't go up to the root/carla logger

    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    # formatting myself
    fh.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(fh)
    return logger

_log = _build_logger()


def _ts() -> str:
    """ISO-8601 timestamp with milliseconds."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


def _write(event: str, detail: str = "") -> None:
    _log.info(f"{_ts()}|{event}|{detail}")


# ----- public API ----- #

def session_start() -> None:
    _write("SESSION_START", f"log={os.path.abspath(LOG_FILE)}")

def session_end() -> None:
    _write("SESSION_END")

def crash(object_hit: str = "unknown") -> None:
    _write("CRASH", object_hit)

def reset() -> None:
    _write("RESET")

def teleport(waypoint_index: int) -> None:
    _write("TELEPORT", f"wp={waypoint_index}")

def waypoint_hit(waypoint_index: int) -> None:
    _write("WAYPOINT_HIT", f"wp={waypoint_index}")

def intervention_start(ai_action: int = -1, q_gap: float = 0.0) -> None:
    _write("INTERVENTION_START", f"action={ai_action} q_gap={q_gap:.3f}")

def intervention_end() -> None:
    _write("INTERVENTION_END")

def mode_change(new_mode: str) -> None:
    _write("MODE_CHANGE", new_mode)
