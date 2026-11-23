import copy
import threading
import time
from collections import OrderedDict

TTL_SECONDS = 3600      # an answer is remembered for 1 hour
MAX_ITEMS = 100         # at most 100 answers; the oldest is dropped first

_store = OrderedDict()
_lock = threading.Lock()


def make_key(question, k, chunk_words):
    return (question.lower(), k, chunk_words)


def get(key):
    with _lock:
        item = _store.get(key)
        if item is None:
            return None
        expires, value = item
        if expires < time.time():
            del _store[key]
            return None
        _store.move_to_end(key)
        return copy.deepcopy(value)


def put(key, value):
    with _lock:
        _store[key] = (time.time() + TTL_SECONDS, copy.deepcopy(value))
        _store.move_to_end(key)
        while len(_store) > MAX_ITEMS:
            _store.popitem(last=False)


def clear():
    with _lock:
        _store.clear()


def size():
    with _lock:
        return len(_store)