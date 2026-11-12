"""Generate original spacecraft ambience and effects with Python's standard library.

The game consumes the same eight PCM16 mono / 22050 Hz WAV names. Loops are
periodic signals with circularly filtered noise, not songs faded to silence.
Run with --check to regenerate in memory and verify every committed byte.
"""
from array import array
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import random
import sys
import wave

RATE = 22050
OUTPUT = Path(__file__).resolve().parents[1] / "audio"
TAU = 2 * math.pi
LOOP_SECONDS = 24
MAX_TOTAL_BYTES = 3 * 1024 * 1024


def lowpass(samples, cutoff, cyclic=False):
    """One-pole filter; solve its initial state for a continuous circular loop."""
    decay = math.exp(-TAU * cutoff / RATE)
    feed = 1 - decay
    state = 0.0
    if cyclic:
        for value in samples:
            state = decay * state + feed * value
        state /= 1 - decay ** len(samples)
    result = []
    for value in samples:
        state = decay * state + feed * value
        result.append(state)
    return result


def noise(seconds, seed, lower, upper, cyclic=False):
    source = random.Random(seed)
    raw = [source.uniform(-1, 1) for _ in range(round(seconds * RATE))]
    high = lowpass(raw, upper, cyclic)
    low = lowpass(high, lower, cyclic)
    return [a - b for a, b in zip(high, low)]


def envelope(time, attack, decay):
    return (1 - math.exp(-time / attack)) * math.exp(-time / decay)


def mix_at(target, sound, seconds, gain=1.0, wrap=False):
    offset = round(seconds * RATE)
    for index, value in enumerate(sound):
        position = offset + index
        if wrap:
            position %= len(target)
        elif position >= len(target):
            break
        target[position] += gain * value


def reflections(sound, taps):
    """Quiet, short reflections supply body without a long arcade echo."""
    result = list(sound)
    for delay, gain in taps:
        mix_at(result, sound, delay, gain)
    return result


def energy_shot():
    duration = .24
    air = noise(duration, 31017, 780, 6200)
    coil = noise(duration, 31018, 80, 1100)
    result = []
    body_phase = arc_phase = 0.0
    for index in range(len(air)):
        time = index / RATE
        body_phase += TAU * (176 + 190 * math.exp(-time * 45)) / RATE
        arc_phase += TAU * (980 + 1100 * math.exp(-time * 95)) / RATE
        crack = 1.5 * air[index] * envelope(time, .0007, .012)
        body = .42 * math.sin(body_phase) * envelope(time, .0015, .037)
        arc = .14 * math.sin(arc_phase + .8 * coil[index]) * envelope(time, .001, .022)
        discharge = .32 * coil[index] * envelope(time, .002, .048)
        result.append(crack + body + arc + discharge)
    return reflections(result, ((.017, .13), (.033, .06)))


def metal_hit():
    duration = .38
    strike = noise(duration, 41127, 480, 7200)
    modes = ((286, .34, .055), (643, .25, .075), (1097, .18, .095),
             (1823, .12, .052), (3231, .07, .030))
    result = []
    for index, grain in enumerate(strike):
        time = index / RATE
        attack = 1 - math.exp(-time / .0007)
        ringing = sum(level * math.sin(TAU * hz * time) * math.exp(-time / decay)
                      for hz, level, decay in modes)
        hull = .22 * math.sin(TAU * 87 * time) * math.exp(-time / .042)
        result.append(attack * (ringing + hull) + 1.3 * grain * envelope(time, .0005, .009))
    return reflections(result, ((.023, .09),))


def hull_damage():
    duration = .78
    rumble = noise(duration, 51029, 24, 480)
    debris = noise(duration, 51030, 1100, 5000)
    result = []
    phase = 0.0
    for index in range(len(rumble)):
        time = index / RATE
        phase += TAU * (43 + 72 * math.exp(-time * 17)) / RATE
        body = .65 * math.sin(phase) * envelope(time, .002, .15)
        pressure = 1.5 * rumble[index] * envelope(time, .003, .18)
        shards = .58 * debris[index] * envelope(time, .001, .022)
        panel = .10 * math.sin(TAU * 169 * time) * envelope(time, .003, .10)
        result.append(body + pressure + shards + panel)
    return reflections(result, ((.043, .12), (.087, .06)))


def transition():
    duration = .92
    vent = noise(duration, 61041, 120, 2200)
    latch = metal_hit()
    result = []
    phase = 0.0
    for index, air in enumerate(vent):
        time = index / RATE
        phase += TAU * (84 + 19 * math.exp(-time * 5)) / RATE
        breath = air * envelope(time, .034, .19)
        hum = .10 * math.sin(phase) * envelope(time, .027, .16)
        result.append(breath + hum)
    mix_at(result, latch, .115, .075)
    return result


def completion(success):
    """A restrained systems cue; no note sequence, arpeggio, or fanfare."""
    duration = 1.35 if success else 1.45
    air = noise(duration, 71053 if success else 71054, 35, 1250)
    result = []
    phase = 0.0
    for index, grain in enumerate(air):
        time = index / RATE
        if success:
            phase += TAU * 104 / RATE
            swell = envelope(time, .045, .28)
            tone = .24 * math.sin(phase) + .09 * math.sin(TAU * 213 * time)
            resonance = .04 * math.sin(TAU * 337 * time) * math.exp(-time / .18)
            result.append(swell * (tone + resonance + .5 * grain))
        else:
            phase += TAU * (31 + 74 * math.exp(-time * 3.8)) / RATE
            power = envelope(time, .003, .30)
            sputter = .7 + .3 * math.sin(TAU * 19 * time) ** 2
            result.append(power * (.42 * math.sin(phase) + .75 * grain * sputter))
    if success:
        latch = metal_hit()
        mix_at(result, latch, .018, .055)
        mix_at(result, latch, .16, .025)
    return result


def mission_pulse():
    duration = .24
    mechanical = noise(duration, 81067, 30, 380)
    result = []
    phase = 0.0
    for index, grain in enumerate(mechanical):
        time = index / RATE
        phase += TAU * (57 + 36 * math.exp(-time * 33)) / RATE
        result.append((.32 * math.sin(phase) + .65 * grain) * envelope(time, .006, .052))
    return result


def ambience(mission):
    """All oscillators have integer cycles per file; filtered noise wraps too."""
    count = LOOP_SECONDS * RATE
    air = noise(LOOP_SECONDS, 91079 if mission else 91078, 85, 1250, True)
    machinery = noise(LOOP_SECONDS, 91081 if mission else 91080, 19, 170, True)
    # Integer cycle counts keep the drone, modulation, and file seam in phase.
    frequencies = (54.75, 82.25, 110.125, 165.375) if mission else (47.5, 95.125, 142.625, 238.75)
    cycles = [round(hz * LOOP_SECONDS) for hz in frequencies]
    amplitudes = (.16, .055, .037, .018) if mission else (.16, .060, .027, .011)
    result = []
    for index in range(count):
        position = index / count
        cycle = TAU * position
        drone = 0.0
        for layer, (turns, level) in enumerate(zip(cycles, amplitudes)):
            modulation = (.11 + layer * .04) * math.sin((layer + 1) * cycle + layer * .9)
            swell = .86 + .14 * math.sin((layer + 1) * cycle + .6 * layer)
            drone += level * swell * math.sin(turns * cycle + modulation + layer * .37)
        ventilation = (.13 + .04 * math.sin(3 * cycle + .4)) * air[index]
        pressure = (.52 + .15 * math.sin(2 * cycle + .7)) * machinery[index]
        result.append(drone + ventilation + pressure)
    if mission:
        pulse = mission_pulse()
        # A muted engine pulse at 75/min; no lead melody or chord progression.
        accents = (1.0, .40, .68, .42, .55, .36)
        for index in range(30):
            mix_at(result, pulse, index * .8 + .12, accents[index % len(accents)] * .23, True)
    return result


def decibels(value):
    return round(20 * math.log10(max(value, 1e-12)), 2)


def prepare(samples, peak_limit, rms_target, looping):
    if not all(math.isfinite(value) for value in samples):
        raise ValueError("Non-finite audio sample.")
    if looping:
        mean = sum(samples) / len(samples)
        signal = [value - mean for value in samples]
    else:
        # A sub-millisecond onset retains the transient; the tail ends at zero.
        onset, ending = max(1, round(.0006 * RATE)), round(.025 * RATE)
        weights = [min(1.0, index / onset, (len(samples) - 1 - index) / ending)
                   for index in range(len(samples))]
        mean = sum(value * weight for value, weight in zip(samples, weights)) / sum(weights)
        signal = [(value - mean) * weight for value, weight in zip(samples, weights)]
    peak = max(abs(value) for value in signal)
    rms = math.sqrt(sum(value * value for value in signal) / len(signal))
    if not peak or not rms:
        raise ValueError("Empty audio signal.")
    gain = min(peak_limit / peak, rms_target / rms)
    pcm = array("h", (round(value * gain * 32767) for value in signal))
    return pcm


def pcm_bytes(pcm):
    if sys.byteorder == "little":
        return pcm.tobytes()
    little = array("h", pcm)
    little.byteswap()
    return little.tobytes()


def wav_bytes(pcm):
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(RATE)
        target.writeframes(pcm_bytes(pcm))
    encoded = output.getvalue()
    with wave.open(io.BytesIO(encoded), "rb") as check:
        assert check.getnchannels() == 1 and check.getsampwidth() == 2
        assert check.getframerate() == RATE and check.getnframes() == len(pcm)
        assert check.readframes(len(pcm)) == pcm_bytes(pcm)
    return encoded


def inspect_clip(name, pcm, encoded, looping):
    peak = max(abs(value) for value in pcm) / 32767
    rms = math.sqrt(sum(value * value for value in pcm) / len(pcm)) / 32767
    dc = sum(pcm) / len(pcm) / 32767
    assert peak < .70 and abs(dc) < .00001, (name, peak, dc)
    result = {
        "file": name + ".wav",
        "seconds": round(len(pcm) / RATE, 3),
        "loop": looping,
        "peak": round(peak, 5),
        "peak_dbfs": decibels(peak),
        "rms": round(rms, 5),
        "rms_dbfs": decibels(rms),
        "crest_db": decibels(peak / rms),
        "dc": round(dc, 8),
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }
    if looping:
        seam_step = abs(pcm[0] - pcm[-1])
        seam_curvature = abs((pcm[1] - pcm[0]) - (pcm[0] - pcm[-1]))
        steps = sorted(abs(pcm[index] - pcm[index - 1]) for index in range(1, len(pcm)))
        ordinary_step = steps[int(.99 * (len(steps) - 1))]
        curves = sorted(abs(pcm[index] - 2 * pcm[index - 1] + pcm[index - 2])
                        for index in range(2, len(pcm)))
        ordinary_curve = curves[int(.99 * (len(curves) - 1))]
        window = round(.1 * RATE)
        left = math.sqrt(sum(value * value for value in pcm[-window:]) / window)
        right = math.sqrt(sum(value * value for value in pcm[:window]) / window)
        assert seam_step <= max(4, ordinary_step * 1.2), (name, seam_step, ordinary_step)
        assert seam_curvature <= max(4, ordinary_curve * 1.2), (name, seam_curvature, ordinary_curve)
        assert .75 < right / left < 1.33, (name, left, right)
        result.update({
            "loop_seam_step": seam_step,
            "loop_seam_dbfs": decibels(seam_step / 32767),
            "loop_p99_step": ordinary_step,
            "loop_seam_curvature": seam_curvature,
            "loop_p99_curvature": ordinary_curve,
            "loop_boundary_rms_ratio": round(right / left, 5),
        })
    else:
        assert pcm[0] == 0 and pcm[-1] == 0, name
    return result


def inspect_mix(clips):
    """Exercise the existing GameAudio .30/.65 gains and tanh limiter offline."""
    length = 8 * RATE
    music = clips["combat"]
    mixed = [music[index % len(music)] * .30 for index in range(length)]
    for index in range(43):
        mix_at(mixed, clips["shot"], index * .18, .65)
    for index in range(9):
        mix_at(mixed, clips["hit"], .4 + index * .8, .65)
    mix_at(mixed, clips["damage"], 2.1, .65)
    mix_at(mixed, clips["transition"], 4.4, .65)
    output = [int(30000 * math.tanh(value / 32768)) for value in mixed]
    peak = max(abs(value) for value in output) / 32767
    rms = math.sqrt(sum(value * value for value in output) / length) / 32767
    assert max(abs(value) for value in output) < 30000
    # Eight coincident voices are the mixer limit; still no PCM clipping.
    stress = [int(30000 * math.tanh((8 * sample * .65 + 32767 * .36 * .30) / 32768))
              for sample in clips["damage"]]
    assert max(abs(value) for value in stress) <= 30000
    return {"scenario_seconds": 8, "peak_dbfs": decibels(peak), "rms_dbfs": decibels(rms),
            "eight_voice_peak_dbfs": decibels(max(abs(value) for value in stress) / 32767),
            "hard_clipped_samples": sum(abs(value) >= 32767 for value in output + stress)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify deterministic bytes without rewriting files.")
    args = parser.parse_args()
    specifications = (
        ("menu", lambda: ambience(False), .32, .085, True),
        ("combat", lambda: ambience(True), .36, .10, True),
        ("shot", energy_shot, .64, .135, False),
        ("hit", metal_hit, .60, .12, False),
        ("damage", hull_damage, .66, .155, False),
        ("victory", lambda: completion(True), .45, .125, False),
        ("defeat", lambda: completion(False), .52, .145, False),
        ("transition", transition, .46, .10, False),
    )
    report, clips = [], {}
    if not args.check:
        OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, synthesizer, peak, rms, looping in specifications:
        pcm = prepare(synthesizer(), peak, rms, looping)
        encoded = wav_bytes(pcm)
        metadata = inspect_clip(name, pcm, encoded, looping)
        path = OUTPUT / (name + ".wav")
        if args.check:
            assert path.read_bytes() == encoded, f"{path.name} differs from its deterministic generator"
        else:
            path.write_bytes(encoded)
        clips[name] = pcm
        report.append(metadata)
        print(f"{path.name:15} {metadata['seconds']:6.2f}s  peak {metadata['peak_dbfs']:6.2f} dBFS  "
              f"RMS {metadata['rms_dbfs']:6.2f} dBFS")
    total = sum(item["bytes"] for item in report)
    assert total < MAX_TOTAL_BYTES, total
    manifest = json.dumps(report, indent=2) + "\n"
    if args.check:
        assert (OUTPUT / "catalogo.json").read_text(encoding="utf-8") == manifest
    else:
        (OUTPUT / "catalogo.json").write_text(manifest, encoding="utf-8")
    print(f"WAV total: {total} bytes; mono PCM16, {RATE} Hz; all format/level/seam checks passed.")
    print("Existing mixer offline simulation: " + json.dumps(inspect_mix(clips), sort_keys=True))
    if args.check:
        print("Deterministic regeneration matches all eight WAV files and catalogo.json.")


if __name__ == "__main__":
    main()
