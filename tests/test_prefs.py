"""Tests for klo_chords.core.prefs — persistent JSON preferences with schema versioning."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

import klo_chords.core.prefs as prefs


@pytest.fixture
def temp_prefs_dir(monkeypatch, tmp_path: Path) -> Path:
    """Redirect _get_dir to a temp directory so tests don't touch real prefs."""
    monkeypatch.setattr(prefs, "_get_dir", lambda: str(tmp_path))
    return tmp_path


class TestDefaults:
    def test_all_keys_present(self):
        d = prefs.DEFAULTS
        expected_keys = {
            "_version", "sound_enabled", "volume", "wave", "audio_quality",
            "legato", "playback_mode", "random_velocity", "vel_min", "vel_max",
            "base_octave", "show_note_names", "show_keybinds", "use_jazz_symbols",
            "sub_oscillator",
            "audio_device",
        }
        assert set(d.keys()) == expected_keys

    def test_version_is_current(self):
        assert prefs.DEFAULTS["_version"] == prefs.CURRENT_VERSION

    def test_volume_range(self):
        assert 0 <= prefs.DEFAULTS["volume"] <= 100
        assert 1 <= prefs.DEFAULTS["vel_min"] <= 127
        assert 1 <= prefs.DEFAULTS["vel_max"] <= 127


class TestLoadDefaults:
    def test_load_when_no_file_returns_defaults(self, temp_prefs_dir):
        data = prefs.load()
        for key, val in prefs.DEFAULTS.items():
            assert data[key] == val

    def test_load_version_is_set(self, temp_prefs_dir):
        data = prefs.load()
        assert data["_version"] == prefs.CURRENT_VERSION


class TestSaveAndLoad:
    def test_round_trip(self, temp_prefs_dir):
        settings = {"volume": 42, "wave": "sine", "_version": 1}
        prefs.save(settings)
        loaded = prefs.load()
        assert loaded["volume"] == 42
        assert loaded["wave"] == "sine"

    def test_missing_keys_filled_from_defaults(self, temp_prefs_dir):
        prefs.save({"volume": 99})
        loaded = prefs.load()
        assert loaded["volume"] == 99
        assert loaded["wave"] == prefs.DEFAULTS["wave"]

    def test_corrupt_json_falls_back_to_defaults(self, temp_prefs_dir):
        path = os.path.join(str(temp_prefs_dir), "preferences.json")
        with open(path, "w") as f:
            f.write("this is not json{{{{")
        data = prefs.load()
        assert data["volume"] == prefs.DEFAULTS["volume"]


class TestMigrations:
    def test_current_version_no_migration_needed(self, temp_prefs_dir):
        data = {"_version": prefs.CURRENT_VERSION, "volume": 50}
        result = prefs._run_migrations(data)
        assert result["volume"] == 50

    def test_zero_version_upgraded(self, temp_prefs_dir):
        data = {"_version": 0, "volume": 50}
        result = prefs._run_migrations(data)
        assert result["_version"] == prefs.CURRENT_VERSION

    def test_migration_preserves_keys(self, temp_prefs_dir):
        data = {"_version": 0, "volume": 77, "legato": False}
        result = prefs._run_migrations(data)
        assert result["volume"] == 77
        assert result["legato"] is False


class TestGetPath:
    def test_returns_existing_file_path(self, temp_prefs_dir):
        path = prefs._get_path()
        assert path.endswith("preferences.json")
        assert os.path.isdir(os.path.dirname(path))


class TestPlatformPaths:
    @mock.patch("sys.platform", "win32")
    def test_windows_path(self):
        d = prefs._get_dir()
        assert "KLO_Chords" in d

    @mock.patch("sys.platform", "darwin")
    def test_macos_path(self):
        d = prefs._get_dir()
        assert "Application Support" in d
        assert "KLO_Chords" in d

    @mock.patch("sys.platform", "linux")
    def test_linux_path(self):
        d = prefs._get_dir()
        assert "KLO_Chords" in d
