import threading

_events: dict[str, threading.Event] = {}


def register(run_id: str) -> threading.Event:
    e = threading.Event()
    _events[run_id] = e
    return e


def request(run_id: str) -> bool:
    e = _events.get(run_id)
    if e:
        e.set()
        return True
    return False


def is_cancelled(run_id: str) -> bool:
    e = _events.get(run_id)
    return e is not None and e.is_set()


def cleanup(run_id: str) -> None:
    _events.pop(run_id, None)
