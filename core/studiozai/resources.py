"""Leave CPU capacity available for playback on small machines."""
import os

from . import config


def cpu_threads():
    cores = os.cpu_count() or 2
    if config.load_settings().get("performance_mode") == "light":
        return 1 if cores <= 4 else 2
    return max(1, min(4, cores // 2))
