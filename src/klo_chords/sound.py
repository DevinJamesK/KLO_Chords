"""
Sound generation and playback for chord notes.

Streaming callback engine that NEVER stops. Uses numpy vectorized
operations in the callback for clean, glitch-free audio.

Wave types: sine, triangle, sawtooth
Playback modes:
  - toggle:  Press toggles on/off. Same chord pressed again = off. New chord = switch.
  - oneshot: Plays ~1 second with natural release tail.
  - legato:  Shared notes between chords are held (not re-struck).
"""

import math
import threading
import random
from typing import List

import sounddevice as sd
import numpy as np

from klo_chords.chords import note_to_pc

SAMPLE_RATE = 44100
BLOCK_SIZE  = 512
MASTER_AMP  = 0.35

ATTACK_S   = 0.008
RELEASE_S  = 0.250
ONESHOT_S  = 0.800


# ── Modes ────────────────────────────────────────────────────────────────────────
MODE_TOGGLE  = "toggle"
MODE_ONESHOT = "oneshot"


# ── Waveform generators ──────────────────────────────────────────────────────────

def _gen_sine(phases):
    return np.sin(phases)

def _gen_triangle(phases):
    p = phases % (2.0 * math.pi)
    t = p / (2.0 * math.pi)
    return 2.0 * np.abs(2.0 * t - 1.0) - 1.0

def _gen_sawtooth(phases):
    p = phases % (2.0 * math.pi)
    t = p / (2.0 * math.pi)
    return 2.0 * t - 1.0

_WAVE_GENS = {
    "sine":      _gen_sine,
    "triangle":  _gen_triangle,
    "sawtooth":  _gen_sawtooth,
}


# ── Voice manager — numpy-friendly state ────────────────────────────────────────

class _VoiceBank:
    """Manages a list of active voices with numpy-friendly block rendering."""
    def __init__(self):
        self.freqs   = np.array([], dtype=np.float64)
        self.amps    = np.array([], dtype=np.float64)
        self.phases  = np.array([], dtype=np.float64)
        self.ages    = np.array([], dtype=np.float64)
        self.release = np.array([], dtype=bool)
        self.oneshot = np.array([], dtype=bool)
        self._dt = 1.0 / SAMPLE_RATE

    def add(self, freq: float, amp: float, is_oneshot: bool):
        self.freqs   = np.append(self.freqs, np.float64(freq))
        self.amps    = np.append(self.amps, np.float64(amp))
        self.phases  = np.append(self.phases, 0.0)
        self.ages    = np.append(self.ages, 0.0)
        self.release = np.append(self.release, False)
        self.oneshot = np.append(self.oneshot, is_oneshot)

    def release_all(self):
        self.release[:] = True
        self.ages[:] = 0.0

    def release_unmatched(self, keep_freqs: List[float]):
        """Release voices whose frequency isn't in keep_freqs (keeps shared notes)."""
        for i in range(len(self.freqs)):
            if not self.release[i] and self.freqs[i] not in keep_freqs:
                self.release[i] = True
                self.ages[i] = 0.0

    def render(self, frames: int, wave_fn, volume: float) -> np.ndarray:
        """Generate a block of *frames* samples."""
        dt = self._dt
        nv = len(self.freqs)
        if nv == 0:
            return np.zeros(frames, dtype=np.float32)

        t = np.arange(frames, dtype=np.float64) * dt
        phases = self.phases[:, np.newaxis] + 2.0 * math.pi * self.freqs[:, np.newaxis] * t[np.newaxis, :]
        wave = wave_fn(phases)
        self.phases = np.float64(phases[:, -1] + 2.0 * math.pi * self.freqs * dt) % (2.0 * math.pi)

        voice_ages = self.ages[:, np.newaxis] + t[np.newaxis, :]

        # Attack envelope
        attack_mask = voice_ages < ATTACK_S
        attack_t = voice_ages / ATTACK_S
        attack_env = attack_t * attack_t * (3.0 - 2.0 * attack_t)

        # Release envelope
        release_mask = self.release[:, np.newaxis]
        release_t = voice_ages / RELEASE_S
        release_env = 1.0 - release_t * release_t * (3.0 - 2.0 * release_t)
        release_env = np.clip(release_env, 0.0, 1.0)

        env = np.where(release_mask, release_env,
                       np.where(attack_mask, attack_env, 1.0))
        env = np.where(release_mask & (voice_ages >= RELEASE_S), 0.0, env)

        # Oneshot auto-release
        oneshot_active = self.oneshot[:, np.newaxis] & ~self.release[:, np.newaxis]
        expired = oneshot_active & (voice_ages >= ONESHOT_S)
        if np.any(expired):
            newly_expired = np.any(expired, axis=1)
            self.ages[newly_expired] = 0.0
            self.release[newly_expired] = True

        mixed = np.sum(wave * env * self.amps[:, np.newaxis] * MASTER_AMP * volume, axis=0)
        self.ages += frames * dt

        alive = ~self.release | (self.ages < RELEASE_S)
        if not np.all(alive):
            self.freqs   = self.freqs[alive]
            self.amps    = self.amps[alive]
            self.phases  = self.phases[alive]
            self.ages    = self.ages[alive]
            self.release = self.release[alive]
            self.oneshot = self.oneshot[alive]

        return mixed.astype(np.float32)

    @property
    def has_voices(self) -> bool:
        return len(self.freqs) > 0 and np.any(~self.release)


# ── Audio engine ─────────────────────────────────────────────────────────────────

class _AudioEngine:
    """Continuous streaming engine. Never stops."""
    def __init__(self):
        self._vb = _VoiceBank()
        self._lock = threading.Lock()
        self._stream: sd.OutputStream = None
        self._mode = MODE_TOGGLE
        self._legato = True             # legato ON by default
        self._note_history: List[str] = []

    def start(self):
        if self._stream is not None:
            return
        try:
            self._stream = sd.OutputStream(
                samplerate=SAMPLE_RATE, channels=1, blocksize=BLOCK_SIZE,
                callback=self._callback, dtype='float32', latency='low',
            )
            self._stream.start()
        except (sd.PortAudioError, OSError) as e:
            # Audio device unavailable — degrade gracefully (no crash).
            print(f"[sound] Warning: could not open audio stream: {e}", flush=True)
            self._stream = None

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            self._vb = _VoiceBank()

    def play_notes(self, frequencies: List[float], amplitudes: List[float],
                   notes: List[str]):
        with self._lock:
            if self._mode == MODE_TOGGLE:
                if notes == self._note_history:
                    # Same chord → toggle off
                    self._vb.release_all()
                    self._note_history = []
                    return
                else:
                    if self._legato:
                        # Keep shared notes held
                        self._vb.release_unmatched(frequencies)
                    else:
                        self._vb.release_all()

            oneshot = (self._mode == MODE_ONESHOT)
            if not self._legato or self._mode == MODE_ONESHOT:
                for freq, amp in zip(frequencies, amplitudes):
                    self._vb.add(freq, amp, oneshot)
            else:
                # Legato: only add frequencies that aren't already playing (and not released)
                # Released voices still linger in self._vb.freqs until the release tail
                # finishes, so we must exclude them from the "already playing" check.
                active_mask = ~self._vb.release
                if np.any(active_mask):
                    active_freqs = self._vb.freqs[active_mask]
                else:
                    active_freqs = np.array([], dtype=np.float64)
                for freq, amp in zip(frequencies, amplitudes):
                    if freq not in active_freqs:
                        self._vb.add(freq, amp, oneshot)

            self._note_history = list(notes)

    def release_all(self):
        with self._lock:
            self._vb.release_all()

    def _callback(self, outdata, frames, time_info, status):
        with self._lock:
            block = self._vb.render(frames, _get_wave_fn(), _volume)
        peak = np.max(np.abs(block))
        if peak > 0.99:
            block = block / peak * 0.95
        outdata[:, 0] = block


# ── Global engine ────────────────────────────────────────────────────────────────

_engine = _AudioEngine()

# ── Settings ─────────────────────────────────────────────────────────────────────

_sound_enabled   = True
_sound_mode      = "triangle"
_random_velocity = True          # ON by default
_velocity_min    = 60
_velocity_max    = 100
_base_octave     = 3
_volume               = 0.75           # global volume 0-1, scales the master amp
_volume_before_mute   = 75             # volume percentage before muting (0-100)


def set_mute(val: bool):
    """Mute/unmute audio. Saves current volume before muting, restores on unmute."""
    global _volume, _volume_before_mute
    if val:
        # Muting — save current volume
        _volume_before_mute = int(round(_volume * 100))
        _volume = 0.0
    else:
        # Unmuting — restore saved volume
        _volume = max(0.0, min(1.0, _volume_before_mute / 100.0))


def is_muted() -> bool:
    """Return True if volume is effectively zero (muted)."""
    return _volume <= 0.0


def _get_wave_fn():
    return _WAVE_GENS.get(_sound_mode, _gen_sine)


def set_enabled(val: bool):
    global _sound_enabled
    _sound_enabled = val
    if not val:
        _engine.release_all()


def set_mode(mode: str):
    global _sound_mode
    _sound_mode = mode


def set_base_octave(octave: int):
    global _base_octave
    _base_octave = max(2, min(6, octave))
    reset_voice_leading()


def set_random_velocity(val: bool):
    global _random_velocity
    _random_velocity = val


def set_velocity_range(vmin: int, vmax: int):
    global _velocity_min, _velocity_max
    _velocity_min = min(vmin, vmax)
    _velocity_max = max(vmin, vmax)


def set_playback_mode(mode: str):
    """Change playback mode and release all active notes.
    
    When switching modes, any currently playing notes are released so
    they don't get stuck (e.g. switching from toggle to oneshot while
    a toggle-latched note is still playing). Note history is also
    cleared so the next toggle press isn't mistaken for a repeat.
    """
    _engine._mode = mode
    _engine.release_all()
    _engine._note_history = []


def set_legato(val: bool):
    """If True, shared notes between chords are held (not re-struck)."""
    _engine._legato = val


def set_volume(val: float):
    global _volume
    _volume = max(0.0, min(1.0, val))


def get_settings() -> dict:
    return dict(
        enabled=_sound_enabled,
        mode=_sound_mode,
        base_octave=_base_octave,
        random_vel=_random_velocity,
        vel_min=_velocity_min,
        vel_max=_velocity_max,
        volume=_volume,
    )


def is_playing() -> bool:
    """Check if any voices are currently active."""
    return _engine._vb.has_voices


def reset_voice_leading():
    global _previous_midi_notes, _current_notes
    _previous_midi_notes = []
    _current_notes = []


# ── Voice-leading state ──────────────────────────────────────────────────────────

_PC_TO_MIDI = {i: i for i in range(12)}
_previous_midi_notes: List[int] = []
_current_notes: List[str] = []


def _equal_loudness_gain(freq: float) -> float:
    if freq <= 0:
        return 1.0
    if freq < 1000:
        g = 10.0 * math.log10(1.0 / (1.0 + ((1000.0 / freq) ** 2.5) * 0.08))
        return 10.0 ** (max(-12, min(0, g)) / 20.0)
    elif freq < 5000:
        return 1.0
    else:
        return max(0.5, 1.0 - (freq - 5000) / 10000.0)


def _midi_to_frequency(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def _target_midi_for_pc(pc: int, target_center: int) -> int:
    base = _PC_TO_MIDI.get(pc, 0)
    best = base + 12
    best_dist = abs(best - target_center)
    for octave in range(0, 9):
        midi = base + 12 * octave
        dist = abs(midi - target_center)
        if dist < best_dist:
            best_dist = dist
            best = midi
    return best


def _voice_chord(notes: List[str]) -> List[int]:
    global _previous_midi_notes
    if not notes:
        _previous_midi_notes = []
        return []
    pcs = [note_to_pc(n) for n in notes]
    anchor = _base_octave * 12 + 21
    if not _previous_midi_notes:
        result = _first_voicing(notes, pcs)
        _previous_midi_notes = list(result)
        return result
    prev = {}
    for mn in _previous_midi_notes:
        pc = mn % 12
        if pc not in prev:
            prev[pc] = mn
    result = []
    for note, pc in zip(notes, pcs):
        if pc in prev:
            result.append(prev[pc])
        else:
            if prev:
                target = sum(prev.values()) // len(prev)
                target = max(anchor - 12, min(anchor + 12, target))
            else:
                target = anchor
            result.append(_target_midi_for_pc(pc, target))
    result = _fix_spacing(result, anchor)
    result = _anti_drift(result, anchor)
    _previous_midi_notes = list(result)
    return result


def _first_voicing(notes, pcs):
    items = sorted(zip(notes, pcs), key=lambda x: x[1])
    centre = _base_octave * 12 + 21
    lo, hi = centre - 12, centre + 12
    midis = []
    for i, (note, pc) in enumerate(items):
        target = centre if len(items) == 1 else lo + (i / (len(items) - 1)) * (hi - lo)
        midis.append(_target_midi_for_pc(pc, int(target)))
    midis = _fix_spacing(midis, centre)
    mp = {pc: m for (_, pc), m in zip(items, midis)}
    return [mp[pc] for pc in pcs]


def _fix_spacing(midis, anchor):
    if len(midis) < 2:
        return list(midis)
    indexed = sorted(enumerate(midis), key=lambda x: x[1])
    changed = True
    for _ in range(10):
        if not changed:
            break
        changed = False
        for i in range(len(indexed) - 1):
            if indexed[i + 1][1] - indexed[i][1] < 3:
                indexed[i + 1] = (indexed[i + 1][0], indexed[i + 1][1] + 12)
                changed = True
        indexed.sort(key=lambda x: x[1])
    r = [0] * len(midis)
    for idx, val in indexed:
        r[idx] = val
    return r


def _anti_drift(midis, anchor):
    if not midis:
        return midis
    drift = (sum(midis) // len(midis)) - anchor
    if abs(drift) > 6:
        return [m + (-12 if drift > 6 else 12) for m in midis]
    return midis


def _get_freqs_and_amps(notes: List[str]):
    midi_notes = _voice_chord(notes)
    freqs = [_midi_to_frequency(m) for m in midi_notes]
    amps = []
    for freq in freqs:
        if _random_velocity:
            vel = random.randint(_velocity_min, _velocity_max) / 127.0
        else:
            vel = 0.7
        amp = vel * _equal_loudness_gain(freq)
        amps.append(amp)
    return freqs, amps


# ── Public playback API ──────────────────────────────────────────────────────────

def play_chord_notes(notes: List[str]):
    """Play chord notes via the streaming engine (never stops)."""
    global _current_notes
    if not _sound_enabled or not notes:
        return
    freqs, amps = _get_freqs_and_amps(notes)
    _current_notes = list(notes)
    _engine.start()
    _engine.play_notes(freqs, amps, notes)


def play_progression_notes(notes: List[str], base_octave: int = 3):
    """Play chord notes for the progression tab with root-position voicing."""
    global _current_notes
    if not _sound_enabled or not notes:
        return
    # Use root-position stacking based on base_octave
    centre = base_octave * 12 + 21
    pcs = [note_to_pc(n) for n in notes]
    midi_notes = []
    for i, pc in enumerate(pcs):
        if i == 0:
            best = pc + 12
            best_dist = abs(best - centre)
            for octave in range(0, 9):
                midi = pc + 12 * octave
                dist = abs(midi - centre)
                if dist < best_dist:
                    best_dist = dist
                    best = midi
        else:
            best = midi_notes[i - 1] + 3
            best_dist = abs(best - (midi_notes[i - 1] + 5))
            for octave in range(0, 9):
                midi = pc + 12 * octave
                if midi >= midi_notes[i - 1] + 3 and midi <= midi_notes[i - 1] + 8:
                    best_dist = 0
                    best = midi
                    break
                elif midi > midi_notes[i - 1] + 3 and midi - (midi_notes[i - 1] + 5) < best_dist:
                    best_dist = abs(midi - (midi_notes[i - 1] + 5))
                    best = midi
        midi_notes.append(best)

    if midi_notes:
        avg = sum(midi_notes) // len(midi_notes)
        drift = avg - centre
        if abs(drift) > 6:
            midi_notes = [m + (-12 if drift > 6 else 12) for m in midi_notes]

    freqs = [_midi_to_frequency(m) for m in midi_notes]
    amps = []
    for freq in freqs:
        if _random_velocity:
            vel = random.randint(_velocity_min, _velocity_max) / 127.0
        else:
            vel = 0.7
        amp = vel * _equal_loudness_gain(freq)
        amps.append(amp)

    _current_notes = list(notes)
    _engine.start()
    _engine.play_notes(freqs, amps, notes)


def stop_current():
    global _current_notes
    _current_notes = []
    _engine.release_all()


def release_note(notes: List[str]):
    global _current_notes
    _current_notes = []
    _engine.release_all()


def get_current_midi_notes() -> List[int]:
    """Return the MIDI note numbers currently being played (sorted ascending)."""
    vb = _engine._vb
    with _engine._lock:
        if len(vb.freqs) == 0:
            return []
        # Get alive (non-released) voices
        alive = ~vb.release
        if not np.any(alive):
            return []
        freqs = vb.freqs[alive]
    # Convert frequencies back to MIDI
    midis = [int(round(69 + 12 * math.log2(f / 440.0))) for f in freqs]
    return sorted(midis)
