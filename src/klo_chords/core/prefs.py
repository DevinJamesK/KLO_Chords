"""
Preferences persistence — JSON file with schema versioning.

Platform-native paths:
  Windows: %LOCALAPPDATA%/KLO_Chords/preferences.json
  macOS:   ~/Library/Application Support/KLO_Chords/preferences.json
  Linux:   ~/.local/share/KLO_Chords/preferences.json

Usage:
  settings = prefs.load()         # dict with defaults filled in
  prefs.save(settings)            # write current state to disk
"""

import json
import os
import sys
from typing import Dict, Any

CURRENT_VERSION = 1

DEFAULTS: Dict[str, Any] = {
    "_version":       CURRENT_VERSION,
    "sound_enabled":  True,
    "volume":         75,
    "wave":           "triangle",
    "audio_quality":  "legacy",
    "legato":         True,
    "playback_mode":  "toggle",
    "random_velocity": True,
    "vel_min":        60,
    "vel_max":        100,
    "base_octave":    3,
    "show_note_names": False,
    "show_keybinds":      True,
    "use_jazz_symbols":   True,
    "sub_oscillator":     True,
    "audio_device":    "system_default",
}

MIGRATIONS: Dict[int, Any] = {
    # When v2 adds new keys:
    # 2: lambda data: {**data, "new_key": "default"},
}


def _get_dir() -> str:
    """Return the platform-specific preferences directory."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    return os.path.join(base, "KLO_Chords")


def _get_path() -> str:
    """Return the full path to preferences.json (ensures directory exists)."""
    d = _get_dir()
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "preferences.json")


def get_path() -> str:
    """Return the full path to preferences.json."""
    return _get_path()


def _run_migrations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply version migrations to bring data up to CURRENT_VERSION."""
    version = data.get("_version", 0)
    while version < CURRENT_VERSION:
        version += 1
        if version in MIGRATIONS:
            data = MIGRATIONS[version](data)
    data["_version"] = CURRENT_VERSION
    return data


def load() -> Dict[str, Any]:
    """Load preferences from disk, or return defaults if missing/corrupt."""
    path = _get_path()
    data: Dict[str, Any] = {}
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
    except (json.JSONDecodeError, OSError):
        data = {}
    data = _run_migrations(data)
    # Fill in any missing keys from defaults
    merged = dict(DEFAULTS)
    merged.update(data)
    merged["_version"] = CURRENT_VERSION
    return merged


def save(settings: Dict[str, Any]) -> None:
    """Persist settings dict to disk."""
    path = _get_path()
    settings["_version"] = CURRENT_VERSION
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, sort_keys=True)
    except OSError as e:
        import sys
        print(f"[prefs] Warning: could not save preferences: {e}", file=sys.stderr)
