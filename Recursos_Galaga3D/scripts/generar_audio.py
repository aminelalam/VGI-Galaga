"""Create original deterministic PCM music and effects for the native game."""
from array import array
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import wave

RATE = 22050
OUTPUT = Path(__file__).resolve().parents[1] / "audio"
TAU = 2 * math.pi


def frequency(note):
    return 440 * 2 ** ((note - 69) / 12)


def tone(buffer, start, length, note, level, attack=.02, release=.12, harmonics=.20):
    offset = round(start * RATE)
    samples = min(round(length * RATE), len(buffer) - offset)
    hz = frequency(note)
    for index in range(max(0, samples)):
        time = index / RATE
        remaining = (samples - 1 - index) / RATE
        envelope = min(1, time / attack, remaining / release)
        signal = math.sin(TAU * hz * time) + harmonics * math.sin(TAU * hz * 2 * time)
        buffer[offset + index] += level * max(0, envelope) * signal


def soundtrack(combat):
    beat = 60 / (132 if combat else 96)
    result = [0.0] * round(32 * beat * RATE)
    roots = (48, 44, 41, 43)
    for bar, root in enumerate(roots):
        start = bar * 8 * beat
        for note in (root, root + 7, root + (4 if bar == 3 else 3)):
            tone(result, start, 8 * beat, note + 12, .11, .4, .45, .08)
        for pulse in range(8):
            tone(result, start + pulse * beat, beat * .78, root - 12, .16, .01, .12, .12)
        melody = (12, 19, 15, 22, 19, 15, 14, 19)
        for index, interval in enumerate(melody):
            tone(result, start + index * beat, beat * .7, root + interval,
                 .075 if combat else .055, .008, .13, .28)
        if combat:
            for pulse in range(16):
                time = start + pulse * beat * .5
                tone(result, time, .055, 90 if pulse % 2 else 78, .022, .002, .05, .05)
            for pulse in range(8):
                tone(result, start + pulse * beat, .15, 33, .09, .003, .12, .02)
    return result


def laser():
    result = []
    phase = 0
    for index in range(round(.12 * RATE)):
        time = index / RATE
        hz = 1150 * math.exp(-time * 13) + 180
        phase += TAU * hz / RATE
        envelope = min(1, time / .003) * math.exp(-time * 33)
        result.append(envelope * (math.sin(phase) + .18 * math.sin(2 * phase)))
    return result


def impact(damage):
    randomizer = random.Random(2301 if damage else 1027)
    duration = .48 if damage else .19
    result = []
    filtered_noise = 0
    phase = 0
    for index in range(round(duration * RATE)):
        time = index / RATE
        filtered_noise += .18 * (randomizer.uniform(-1, 1) - filtered_noise)
        phase += TAU * (55 + 180 * math.exp(-time * 18)) / RATE
        envelope = min(1, time / .003) * math.exp(-time * (8 if damage else 22))
        result.append(envelope * (.6 * filtered_noise + .35 * math.sin(phase)))
    return result


def phrase(notes, spacing, duration):
    result = [0.0] * round(duration * RATE)
    for index, note in enumerate(notes):
        tone(result, index * spacing, spacing * 2, note, .5, .012, .15, .22)
    return result


def save(name, samples, peak):
    # A short fade at both file edges prevents clicks at playback and loop seams.
    fade = min(round(.015 * RATE), len(samples) // 2)
    for index in range(fade):
        gain = index / fade
        samples[index] *= gain
        samples[-1 - index] *= gain
    amplitude = max(abs(sample) for sample in samples)
    assert amplitude > 0 and all(math.isfinite(sample) for sample in samples)
    gain = peak * 32767 / amplitude
    pcm = array("h", (round(sample * gain) for sample in samples))
    if sys.byteorder != "little":
        pcm.byteswap()
    path = OUTPUT / f"{name}.wav"
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(RATE)
        target.writeframes(pcm.tobytes())
    with wave.open(str(path), "rb") as check:
        assert check.getnchannels() == 1 and check.getsampwidth() == 2
        assert check.getframerate() == RATE and check.getnframes() == len(pcm)
        assert check.readframes(check.getnframes()) == pcm.tobytes()
    maximum = max(abs(value) for value in pcm)
    assert maximum < 32767 and pcm[0] == 0 and pcm[-1] == 0
    return {"file": path.name, "seconds": round(len(pcm) / RATE, 3),
            "peak": round(maximum / 32767, 4),
            "rms": round(math.sqrt(sum(value * value for value in pcm) / len(pcm)) / 32767, 4),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    clips = {
        "menu": (soundtrack(False), .38),
        "combat": (soundtrack(True), .40),
        "shot": (laser(), .52),
        "hit": (impact(False), .56),
        "damage": (impact(True), .61),
        "victory": (phrase((60, 64, 67, 72, 76, 79), .18, 1.6), .53),
        "defeat": (phrase((55, 51, 48, 43), .3, 1.8), .48),
        "transition": (phrase((60, 67, 72), .14, .8), .40),
    }
    report = [save(name, samples, peak) for name, (samples, peak) in clips.items()]
    (OUTPUT / "catalogo.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
