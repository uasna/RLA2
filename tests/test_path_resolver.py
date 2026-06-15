"""
tests/test_path_resolver.py
Pruebas del Path Resolver para el Punto 1.

Ejecutar desde la raíz del proyecto:
    python tests/test_path_resolver.py

No requiere pytest. Funciona en Windows y Linux (útil para CI).
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Añadir raíz del proyecto al path para importar sin instalar
sys.path.insert(0, str(Path(__file__).parent.parent))

from rla_app.config.paths import RLPathResolver, _build_replay_candidates, _build_log_candidates, _build_training_candidates
from rla_app.core.errors import PathResolutionError, AppDataInitError
from rla_app.core.models import ResolvedRocketLeaguePaths


class TestPathResolver(unittest.TestCase):

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _make_fake_env(self, tmpdir: Path) -> dict[str, str]:
        """Crea un entorno simulado con USERPROFILE apuntando a tmpdir."""
        return {
            "USERPROFILE": str(tmpdir),
            "HOME": str(tmpdir),
        }

    # ── Test 1: Resuelve ruta de replays en Documents normal ─────────────────

    def test_resolves_demos_dir_no_onedrive(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            demos = tmpdir / "Documents" / "My Games" / "Rocket League" / "TAGame" / "Demos"
            demos.mkdir(parents=True)

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                resolver = RLPathResolver()
                paths = resolver.resolve()

            self.assertIsNotNone(paths.replays_dir, "Debe encontrar la carpeta Demos")
            self.assertTrue(paths.replays_ok)
            self.assertIn("Demos", str(paths.replays_dir))

    # ── Test 2: Prefiere DemosEpic sobre Demos ───────────────────────────────

    def test_prefers_demos_epic_over_demos(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            base = tmpdir / "Documents" / "My Games" / "Rocket League" / "TAGame"
            demos = base / "Demos"
            demos_epic = base / "DemosEpic"
            demos.mkdir(parents=True)
            demos_epic.mkdir(parents=True)

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                paths = RLPathResolver().resolve()

            self.assertIsNotNone(paths.replays_dir)
            self.assertIn("DemosEpic", str(paths.replays_dir),
                          "DemosEpic debe tener prioridad sobre Demos")

    # ── Test 3: Prefiere OneDrive sobre Documents local ──────────────────────

    def test_prefers_onedrive_over_local_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            base_local = tmpdir / "Documents" / "My Games" / "Rocket League" / "TAGame"
            base_od = tmpdir / "OneDrive" / "Documents" / "My Games" / "Rocket League" / "TAGame"
            (base_local / "DemosEpic").mkdir(parents=True)
            (base_od / "DemosEpic").mkdir(parents=True)

            env = self._make_fake_env(tmpdir)
            with patch.dict(os.environ, env, clear=False):
                paths = RLPathResolver().resolve()

            self.assertIsNotNone(paths.replays_dir)
            self.assertIn("OneDrive", str(paths.replays_dir),
                          "OneDrive debe tener prioridad sobre Documents local")

    # ── Test 4: Sin replays → error controlado, no crash ─────────────────────

    def test_no_replay_dir_returns_error_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            # No creamos ninguna carpeta de replays

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                paths = RLPathResolver().resolve()

            self.assertIsNone(paths.replays_dir)
            self.assertFalse(paths.replays_ok)
            self.assertTrue(len(paths.errors) > 0, "Debe haber al menos un error reportado")
            print(f"  [OK] Error controlado: {paths.errors[0]}")

    # ── Test 5: App data se crea automáticamente ─────────────────────────────

    def test_app_data_created_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            docs = tmpdir / "Documents"
            docs.mkdir()

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                paths = RLPathResolver().resolve()

            self.assertTrue(paths.app_data_dir.exists())
            self.assertTrue(paths.app_logs_dir.exists())
            self.assertTrue(paths.app_replay_json_dir.exists())
            self.assertTrue(paths.app_cache_dir.exists())
            self.assertTrue(paths.app_training_bank_dir.exists())
            print(f"  [OK] App data en: {paths.app_data_dir}")

    # ── Test 6: Resuelve Launch.log ──────────────────────────────────────────

    def test_resolves_launch_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            log_dir = (
                tmpdir / "Documents" / "My Games" / "Rocket League" / "TAGame" / "Logs"
            )
            log_dir.mkdir(parents=True)
            (log_dir / "Launch.log").write_text("fake log content")

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                paths = RLPathResolver().resolve()

            self.assertTrue(paths.logs_ok)
            self.assertIsNotNone(paths.logs_file)
            print(f"  [OK] Log encontrado: {paths.logs_file}")

    # ── Test 7: Sin Launch.log → warning, no error crítico ───────────────────

    def test_no_launch_log_is_warning_not_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "Documents").mkdir()

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                paths = RLPathResolver().resolve()

            self.assertFalse(paths.logs_ok)
            has_warning = any("Launch.log" in w or "log" in w.lower() for w in paths.warnings)
            self.assertTrue(has_warning, "Debe haber un warning sobre el log faltante")

    # ── Test 8: Training no encontrado → warning, no error ───────────────────

    def test_no_training_dir_is_warning_not_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "Documents").mkdir()

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                paths = RLPathResolver().resolve()

            self.assertFalse(paths.training_ok)

    # ── Test 9: summary_lines() genera output legible ────────────────────────

    def test_summary_lines_not_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "Documents").mkdir()

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                paths = RLPathResolver().resolve()

            lines = paths.summary_lines()
            self.assertTrue(len(lines) >= 5)
            # Verificar que contiene las secciones esperadas
            joined = "\n".join(lines)
            self.assertIn("Replays", joined)
            self.assertIn("App data", joined)

    # ── Test 10: USERPROFILE ausente → PathResolutionError ───────────────────

    def test_missing_userprofile_raises_controlled_error(self):
        from rla_app.config.paths import _user_profile
        env_without = {k: v for k, v in os.environ.items()
                       if k not in ("USERPROFILE", "HOME")}
        with patch.dict(os.environ, env_without, clear=True):
            with self.assertRaises(PathResolutionError):
                _user_profile()

    # ── Test 11: Training dir nunca se crea si no existe ─────────────────────

    def test_training_dir_never_created_by_resolver(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "Documents").mkdir()

            training_path = (
                tmpdir / "Documents" / "My Games" / "Rocket League"
                / "TAGame" / "Training" / "0000000000000000" / "MyTraining"
            )

            with patch.dict(os.environ, self._make_fake_env(tmpdir), clear=False):
                RLPathResolver().resolve()

            self.assertFalse(
                training_path.exists(),
                "El Path Resolver NO debe crear la carpeta de training de RL"
            )

    # ── Test 12: OneDrive via variable de entorno ─────────────────────────────

    def test_onedrive_env_variable_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            od_docs = tmpdir / "MyOneDrive" / "Documents"
            demos = od_docs / "My Games" / "Rocket League" / "TAGame" / "DemosEpic"
            demos.mkdir(parents=True)

            env = self._make_fake_env(tmpdir)
            env["OneDrive"] = str(tmpdir / "MyOneDrive")
            with patch.dict(os.environ, env, clear=False):
                paths = RLPathResolver().resolve()

            self.assertIsNotNone(paths.replays_dir)
            self.assertIn("MyOneDrive", str(paths.replays_dir))
            print(f"  [OK] OneDrive via env var: {paths.replays_dir}")


# ── Runner manual con output detallado ───────────────────────────────────────

def run_manual_demo() -> None:
    """
    Ejecuta el resolver contra el entorno REAL del sistema.
    Útil para verificar en una máquina con Rocket League instalado.
    """
    print("\n" + "═" * 60)
    print("  RLA 2 — Path Resolver DEMO (entorno real)")
    print("═" * 60)

    resolver = RLPathResolver()
    paths = resolver.resolve()

    for line in paths.summary_lines():
        print(line)

    print("\n── REPLAY CANDIDATES ──────────────────────────────────────")
    for probe in paths.probed_replays:
        mark = "✓" if probe.exists else "✗"
        print(f"  {mark} [{probe.label}]")
        print(f"      {probe.path}")

    print("\n── LOG CANDIDATES ─────────────────────────────────────────")
    for probe in paths.probed_logs:
        mark = "✓" if probe.exists else "✗"
        print(f"  {mark} [{probe.label}]")
        print(f"      {probe.path}")

    print("\n── TRAINING CANDIDATES ────────────────────────────────────")
    for probe in paths.probed_training:
        mark = "✓" if probe.exists else "✗"
        print(f"  {mark} [{probe.label}]")
        print(f"      {probe.path}")

    print("\n── APP DATA ───────────────────────────────────────────────")
    subdirs = [
        ("DB",         paths.app_db_path),
        ("Logs",       paths.app_logs_dir),
        ("JSON out",   paths.app_replay_json_dir),
        ("Cache",      paths.app_cache_dir),
        ("Train bank", paths.app_training_bank_dir),
    ]
    for label, p in subdirs:
        mark = "✓" if p.exists() else "✗"
        print(f"  {mark} {label:12}: {p}")
    print()


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_manual_demo()
    else:
        # Primero demo real, luego tests unitarios
        run_manual_demo()
        print("\n" + "═" * 60)
        print("  UNIT TESTS")
        print("═" * 60 + "\n")
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestPathResolver)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
