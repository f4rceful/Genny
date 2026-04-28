"""Управление отменой генерации: хранит threading.Event для каждого run_id."""
import threading


class CancelledError(Exception):
    pass


# Глобальный словарь событий отмены: run_id → Event
_events: dict[str, threading.Event] = {}


def register(run_id: str) -> threading.Event:
    """Создаёт событие отмены для нового запуска."""
    e = threading.Event()
    _events[run_id] = e
    return e


def request(run_id: str) -> bool:
    """Устанавливает флаг отмены; возвращает False если запуск не найден."""
    e = _events.get(run_id)
    if e:
        e.set()
        return True
    return False


def is_cancelled(run_id: str) -> bool:
    e = _events.get(run_id)
    return e is not None and e.is_set()


def cleanup(run_id: str) -> None:
    """Удаляет событие из памяти после завершения запуска."""
    _events.pop(run_id, None)
