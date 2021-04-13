# -*- coding: utf-8 -*-
import time


def timestamp_ms():
    """Ruturn timestamp in milisecond."""
    return int(time.time() * 1000)


def timestamp_mics():
    """Return timestamp in microseconds."""
    return int(time.time() * 1000000)
