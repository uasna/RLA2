"""
RLA 2 — app/event_bus.py
Bus de eventos liviano basado en threading.
Los suscriptores reciben AppEvent en el hilo que publica (sync).
Para la UI, los suscriptores deben hacer su propio marshal al hilo de tkinter.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable

from rla_app.core.models import AppEvent, AppEventCategory, AppEventLevel

_logger = logging.getLogger("rla.event_bus")


class EventBus:
    """
    Bus de eventos simple con suscriptores callback.

    Hilo-seguro para publicar desde cualquier hilo.
    Los callbacks se ejecutan en el hilo del publicador.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handlers: list[Callable[[AppEvent], None]] = []

    def subscribe(self, handler: Callable[[AppEvent], None]) -> None:
        """Registra un handler que recibirá todos los eventos."""
        with self._lock:
            self._handlers.append(handler)

    def unsubscribe(self, handler: Callable[[AppEvent], None]) -> None:
        with self._lock:
            self._handlers = [h for h in self._handlers if h is not handler]

    def publish(self, event: AppEvent) -> None:
        """Publica un evento a todos los handlers registrados."""
        _logger.log(
            _level_to_logging(event.level),
            "[%s] %s",
            event.category.value,
            event.message,
        )
        with self._lock:
            handlers = list(self._handlers)
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001
                _logger.error("Handler de evento falló: %s", exc)

    # ── Helpers de conveniencia ───────────────────────────────────────────────

    def info(self, category: AppEventCategory, message: str, **payload) -> None:
        self.publish(AppEvent(AppEventLevel.INFO, category, message, payload=payload))

    def warning(self, category: AppEventCategory, message: str, **payload) -> None:
        self.publish(AppEvent(AppEventLevel.WARNING, category, message, payload=payload))

    def error(self, category: AppEventCategory, message: str, **payload) -> None:
        self.publish(AppEvent(AppEventLevel.ERROR, category, message, payload=payload))

    def debug(self, category: AppEventCategory, message: str, **payload) -> None:
        self.publish(AppEvent(AppEventLevel.DEBUG, category, message, payload=payload))


def _level_to_logging(level: AppEventLevel) -> int:
    return {
        AppEventLevel.DEBUG:   logging.DEBUG,
        AppEventLevel.INFO:    logging.INFO,
        AppEventLevel.WARNING: logging.WARNING,
        AppEventLevel.ERROR:   logging.ERROR,
    }.get(level, logging.INFO)


# Instancia global de la aplicación
_bus: EventBus | None = None


def get_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
