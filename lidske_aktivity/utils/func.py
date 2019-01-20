import logging
import random
import time
from functools import wraps
from threading import Event

logger = logging.getLogger(__name__)


def measure_time(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        time_start = time.time()
        ret = f(*args, **kwargs)
        duration = time.time() - time_start
        logger.info('Called %s in %f s', f.__name__, duration)
        return ret
    return wrapper


def random_wait(event_stop: Event, min_sec: int = 1, max_sec: int = 20):
    for _ in range(random.randint(1, 20)):
        if event_stop.is_set():
            logger.warning('Stopping test sleep')
            break
        time.sleep(1)
