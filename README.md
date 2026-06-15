# Rocket League Analyzer 2 (RLA 2)

> Motor local de análisis post-partido para Rocket League en Windows.
> Construido desde cero con Clean Architecture. Sin parches del prototipo anterior.

## Estado actual

| Punto | Módulo | Estado |
|-------|--------|--------|
| 1 | Path Resolver (OneDrive / sin OneDrive) | ✅ Completo |
| 2 | Watcher de replays | 🔜 Siguiente |
| 3 | SQLite Storage | 🔜 Pendiente |
| 4 | Event Bus / Logging | 🔜 Pendiente |
| 5 | MMR Service + fallback manual | 🔜 Pendiente |
| 6 | Parser Service (stub seguro) | 🔜 Pendiente |
| 7 | Training Pack Safety Layer | 🔜 Pendiente |
| 8 | Empaquetado Windows `.exe` | 🔜 Pendiente |
| 9 | UI piloto CustomTkinter | 🔜 Pendiente |
| 10 | README final + GitHub prep | 🔜 Pendiente |

## Requisitos

- Windows 10/11
- Python 3.11+
- Rocket League instalado y ejecutado al menos una vez

## Instalación rápida

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar

```bash
python -m rla_app
```

## Probar Path Resolver (Punto 1)

```bash
python tests/test_path_resolver.py
```

## Rutas detectadas automáticamente

RLA 2 detecta rutas en este orden de prioridad:

### Replays
1. `%USERPROFILE%\OneDrive\Documents\My Games\Rocket League\TAGame\DemosEpic`
2. `%USERPROFILE%\OneDrive\Documents\My Games\Rocket League\TAGame\Demos`
3. `%USERPROFILE%\Documents\My Games\Rocket League\TAGame\DemosEpic`
4. `%USERPROFILE%\Documents\My Games\Rocket League\TAGame\Demos`

También respeta la variable de entorno `OneDrive` si está definida.

### Datos internos de RLA

Creados automáticamente en:
```
%USERPROFILE%\Documents\My Games\RLA\
  app.db
  logs/
  replay_json/
  cache/
  training_template_bank/
```

## Reglas de seguridad de Training Packs

- **Nunca** se borra `Training/` ni `MyTraining/`.
- **Nunca** se sobrescriben packs del usuario sin backup explícito.
- La mutación binaria `.Tem` está **bloqueada** hasta que exista un writer validado.
- Toda instalación tiene modo `dry_run=True` por defecto.

## Arquitectura

```
rla_app/
  core/          # Modelos puros, errores, protocolos — zero deps externas
  config/        # Path Resolver, Settings
  app/           # Event Bus, Bootstrap
  utils/         # Logging
  (resto en construcción por puntos)
```

---
*RLA 2 — No hereda código de RLA 1.*
