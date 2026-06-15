"""
RLA 2 — core/errors.py
Jerarquía de errores controlados.  Sin dependencias externas.
"""


class RLAError(Exception):
    """Raíz de todos los errores de la aplicación."""


# ── Path / Config ───────────────────────────────────────────────────────────

class PathResolutionError(RLAError):
    """No se pudo resolver ninguna ruta válida para un recurso requerido."""


class PathNotFoundError(PathResolutionError):
    """Una ruta que debería existir no existe en disco."""


class AppDataInitError(RLAError):
    """No se pudo inicializar la carpeta de datos internos de RLA."""


# ── Training Pack Safety ─────────────────────────────────────────────────────

class UnsupportedOperationError(RLAError):
    """
    Operación solicitada que está explícitamente bloqueada por política de
    seguridad de RLA 2 (p.ej. mutación binaria sin writer validado).
    """


class TrainingSafetyViolation(RLAError):
    """Intento de operación que violaría las reglas de seguridad de training."""


# ── MMR ──────────────────────────────────────────────────────────────────────

class MmrFetchError(RLAError):
    """No se pudo obtener el MMR desde ninguna fuente de red."""


class MmrNotConfiguredError(RLAError):
    """No hay Epic ID configurado, no es posible consultar MMR."""


# ── Parser ───────────────────────────────────────────────────────────────────

class ParserNotConfiguredError(RLAError):
    """No hay ejecutable de parser configurado."""


class ParserExecutionError(RLAError):
    """El parser externo devolvió un error o falló inesperadamente."""


# ── Storage ──────────────────────────────────────────────────────────────────

class StorageError(RLAError):
    """Error genérico de la capa de persistencia."""


class MigrationError(StorageError):
    """Fallo durante la migración del esquema SQLite."""
