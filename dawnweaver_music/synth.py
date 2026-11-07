"""Small numpy synthesizer used to render the Dawn Weaver battle music.

Everything is synthesized from scratch (no samples, no external services).
Songs are described as note events in beats; the same events are exported to MIDI.
"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
NOTE_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi_of(name):
    """'C#5' / 'Bb4' -> midi number."""
    n = NOTE_NAMES[name[0]]
    i = 1
    while i < len(name) and name[i] in "#b":
        n += 1 if name[i] == "#" else -1
        i += 1
    return n + 12 * (int(name[i:]) + 1)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def parse_line(text, start_beat=0.0):
    """'A4:1.5 D5:.5 r:1' -> [(beat, dur, midi)]"""
    out, t = [], start_beat
    for tok in text.split():
        n, d = tok.split(":")
        d = float(d)
        if n != "r":
            out.append((t, d, midi_of(n)))
        t += d
    return out


# ---------------------------------------------------------------- utilities
def lp(x, cutoff, order=2):
    sos = butter(order, min(cutoff, SR * 0.45), "low", fs=SR, output="sos")
    return sosfilt(sos, x)


def hp(x, cutoff, order=2):
    sos = butter(order, cutoff, "high", fs=SR, output="sos")
    return sosfilt(sos, x)


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, min(hi, SR * 0.45)], "band", fs=SR, output="sos")
    return sosfilt(sos, x)


def adsr(n, a, d, s, r, sustain_n=None):
    a, d, r = int(a * SR) + 1, int(d * SR) + 1, int(r * SR) + 1
    hold = n if sustain_n is None else sustain_n
    env = np.full(n, s, dtype=np.float64)
    ai = min(a, n)
    env[:ai] = np.linspace(0, 1, a)[:ai]
    if a < n:
        di = min(d, n - a)
        env[a:a + di] = np.linspace(1, s, d)[:di]
    if hold < n:
        level = env[hold - 1] if hold > 0 else 0
        rel = np.linspace(level, 0, r)
        m = min(r, n - hold)
        env[hold:hold + m] = rel[:m]
        env[hold + m:] = 0
    return env


def saw(phase):
    return 2.0 * (phase - np.floor(phase + 0.5))


def osc_phase(f, n, vib_rate=0.0, vib_depth=0.0, delay=0.15):
    t = np.arange(n) / SR
    if vib_depth:
        ramp = np.clip((t - delay) / 0.3, 0, 1)
        f = f * (1 + vib_depth * ramp * np.sin(2 * np.pi * vib_rate * t))
        return np.cumsum(f) / SR
    return f * t


rng = np.random.default_rng(7)


# ---------------------------------------------------------------- instruments
def strings_legato(f, dur, vel, bright=3500):
    n = int((dur + 0.5) * SR)
    out = np.zeros(n)
    for det in (-0.006, -0.002, 0.003, 0.007):
        ph = osc_phase(f * (1 + det), n, 5.2, 0.004)
        out += saw(ph + rng.random())
    out = lp(out, bright, 2)
    env = adsr(n, 0.09, 0.2, 0.85, 0.35, int(dur * SR))
    return out * env * vel * 0.18


def strings_stacc(f, dur, vel, bright=4200):
    d = min(dur, 0.16)
    n = int((d + 0.12) * SR)
    out = np.zeros(n)
    for det in (-0.004, 0.0, 0.005):
        out += saw(osc_phase(f * (1 + det), n) + rng.random())
    out = lp(out, bright, 2)
    env = adsr(n, 0.006, 0.07, 0.45, 0.08, int(d * SR))
    return out * env * vel * 0.22


def brass(f, dur, vel, bright=1.0):
    n = int((dur + 0.3) * SR)
    ph = osc_phase(f, n, 5.0, 0.003, 0.25)
    raw = saw(ph) + 0.6 * saw(ph * 1.003 + 0.3)
    # filter that opens on attack ("blat") and follows note-on
    t = np.arange(n) / SR
    cut_env = 600 + bright * (2600 * vel) * (1 - np.exp(-t / 0.05)) * (0.75 + 0.25 * np.exp(-t / 0.4))
    # time-varying filter approximated by blending two static filters
    lo_b = lp(raw, 700, 2)
    hi_b = lp(raw, 700 + bright * 3200 * vel, 2)
    w = np.clip((cut_env - 600) / (bright * 2600 * vel + 1e-9), 0, 1)
    out = lo_b * (1 - w) + hi_b * w
    env = adsr(n, 0.035, 0.15, 0.8, 0.2, int(dur * SR))
    return out * env * vel * 0.3


def flute(f, dur, vel):
    n = int((dur + 0.25) * SR)
    ph = osc_phase(f, n, 5.5, 0.006, 0.2)
    tone = np.sin(2 * np.pi * ph) + 0.25 * np.sin(4 * np.pi * ph) + 0.08 * np.sin(6 * np.pi * ph)
    breath = bp(rng.standard_normal(n), f * 0.8, f * 3) * 0.08
    env = adsr(n, 0.04, 0.1, 0.85, 0.15, int(dur * SR))
    return (tone + breath) * env * vel * 0.32


def pluck(f, dur, vel, decay=0.996):
    """Karplus-Strong harp/pluck."""
    n = int((min(dur, 1.6) + 0.8) * SR)
    p = max(2, int(SR / f))
    buf = lp(rng.standard_normal(p), min(f * 8, 9000), 1)
    out = np.zeros(n)
    reps = n // p + 1
    y = np.tile(buf, 1)
    blocks = []
    cur = buf.copy()
    for _ in range(reps):
        blocks.append(cur)
        cur = decay * 0.5 * (cur + np.roll(cur, 1))
    out = np.concatenate(blocks)[:n]
    env = adsr(n, 0.002, 0.05, 1.0, 0.3, int((min(dur, 1.6) + 0.5) * SR))
    return out * env * vel * 0.5


def bass(f, dur, vel):
    n = int((dur + 0.08) * SR)
    ph = osc_phase(f, n)
    out = lp(saw(ph), 900, 2) + 0.7 * np.sin(2 * np.pi * ph)
    env = adsr(n, 0.004, 0.12, 0.7, 0.05, int(dur * 0.92 * SR))
    return out * env * vel * 0.35


def choir(f, dur, vel):
    n = int((dur + 0.6) * SR)
    raw = np.zeros(n)
    for det in (-0.005, 0.0, 0.006):
        raw += saw(osc_phase(f * (1 + det), n, 4.6, 0.005) + rng.random())
    out = bp(raw, 600, 850) * 1.0 + bp(raw, 1000, 1250) * 0.6 + bp(raw, 2400, 2800) * 0.25
    env = adsr(n, 0.35, 0.3, 0.9, 0.55, int(dur * SR))
    return out * env * vel * 0.5


def organ(f, dur, vel):
    n = int((dur + 0.3) * SR)
    ph = osc_phase(f, n)
    out = sum(a * np.sin(2 * np.pi * ph * h) for h, a in ((0.5, 0.5), (1, 1), (2, 0.5), (3, 0.25), (4, 0.2)))
    env = adsr(n, 0.05, 0.1, 0.9, 0.25, int(dur * SR))
    return out * env * vel * 0.12


def bell(f, dur, vel):
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    out = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dcy)
              for r, a, dcy in ((1, 1, 1.6), (2.76, 0.5, 2.5), (5.4, 0.25, 4), (8.9, 0.12, 6)))
    return out * vel * 0.18 * np.minimum(1, t / 0.002)


# ---------------------------------------------------------------- drums
def kick(vel=1.0):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    click = lp(rng.standard_normal(n), 3000) * np.exp(-t / 0.004) * 0.3
    return (body + click) * vel * 0.8


def snare(vel=1.0):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.5
    noise = bp(rng.standard_normal(n), 1500, 9000) * np.exp(-t / 0.09)
    return (tone + noise) * vel * 0.45


def hat(vel=1.0, open_=False):
    n = int((0.35 if open_ else 0.08) * SR)
    t = np.arange(n) / SR
    out = hp(rng.standard_normal(n), 7000) * np.exp(-t / (0.12 if open_ else 0.02))
    return out * vel * 0.18


def crash(vel=1.0):
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    out = hp(rng.standard_normal(n), 4000) * np.exp(-t / 0.7)
    return out * vel * 0.22


def timpani(f, vel=1.0):
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    pitch = f * (1 + 0.04 * np.exp(-t / 0.05))
    ph = np.cumsum(pitch) / SR
    out = (np.sin(2 * np.pi * ph) + 0.5 * np.sin(2 * np.pi * ph * 1.5) * np.exp(-t / 0.2)
           + 0.3 * np.sin(2 * np.pi * ph * 1.99) * np.exp(-t / 0.3)) * np.exp(-t / 0.55)
    out += lp(rng.standard_normal(n), 900) * np.exp(-t / 0.02) * 0.4
    return out * vel * 0.65


def taiko(vel=1.0):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = 70 + 60 * np.exp(-t / 0.04)
    out = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    out += lp(rng.standard_normal(n), 1200) * np.exp(-t / 0.03) * 0.5
    return out * vel * 0.85


def swell(length_s, vel=1.0):
    """Reverse cymbal / riser."""
    n = int(length_s * SR)
    t = np.arange(n) / SR
    out = hp(rng.standard_normal(n), 3500) * (t / length_s) ** 2.5
    return out * vel * 0.25


# ---------------------------------------------------------------- mixing
class Mix:
    def __init__(self, seconds, bpm):
        self.bpm = bpm
        self.spb = 60.0 / bpm
        self.n = int(seconds * SR)
        self.buses = {}

    def bus(self, name):
        if name not in self.buses:
            self.buses[name] = np.zeros((2, self.n))
        return self.buses[name]

    def add(self, name, sig, beat, pan=0.0, gain=1.0):
        b = self.bus(name)
        i = int(round(beat * self.spb * SR))
        if i >= self.n:
            return
        sig = sig[: self.n - i] * gain
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        b[0, i:i + len(sig)] += sig * l
        b[1, i:i + len(sig)] += sig * r

    def notes(self, name, inst, events, pan=0.0, gain=1.0, vel=0.8, **kw):
        for (beat, dur, m) in events:
            self.add(name, inst(hz(m), dur * self.spb, vel, **kw), beat, pan, gain)


def make_ir(seconds=2.4, decay=0.55, seed=3):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n))
    for c in range(2):
        noise = r.standard_normal(n)
        noise = lp(noise, 6500, 1)
        ir[c] = noise * np.exp(-t / decay) * np.minimum(1, t / 0.012)
        ir[c, : int(0.012 * SR)] *= 0.3
        ir[c] /= np.sqrt(np.sum(ir[c] ** 2))
    return ir


def reverb(stereo, wet, ir):
    out = np.zeros((2, stereo.shape[1] + ir.shape[1] - 1))
    for c in range(2):
        out[c] = fftconvolve(stereo[c], ir[c])
    dry = np.zeros_like(out)
    dry[:, : stereo.shape[1]] = stereo
    return dry + out * wet


def master(stereo, target_peak=0.89, drive=1.4):
    x = stereo / (np.max(np.abs(stereo)) + 1e-9)
    x = np.tanh(x * drive) / np.tanh(drive)
    x = hp(x, 28, 2)
    return x / np.max(np.abs(x)) * target_peak


def fold_loop(stereo, loop_n):
    """Wrap everything after the loop point back onto the start (seamless loop)."""
    out = stereo[:, :loop_n].copy()
    pos = loop_n
    while pos < stereo.shape[1]:
        seg = stereo[:, pos:pos + loop_n]
        out[:, : seg.shape[1]] += seg
        pos += loop_n
    return out


def write_wav(path, stereo):
    from scipy.io import wavfile
    data = (np.clip(stereo.T, -1, 1) * 32767).astype(np.int16)
    wavfile.write(path, SR, data)


def write_midi(path, bpm, tracks):
    """tracks: list of (name, program, channel, events[(beat, dur, midi, vel?)])"""
    import mido
    mid = mido.MidiFile(ticks_per_beat=480)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    mid.tracks.append(meta)
    for name, program, ch, events in tracks:
        tr = mido.MidiTrack()
        tr.append(mido.MetaMessage("track_name", name=name, time=0))
        if ch != 9:
            tr.append(mido.Message("program_change", program=program, channel=ch, time=0))
        msgs = []
        for ev in events:
            beat, dur, m = ev[:3]
            v = int(ev[3] * 127) if len(ev) > 3 else 96
            msgs.append((int(beat * 480), 1, m, v))
            msgs.append((int((beat + dur) * 480) - 1, 0, m, 0))
        msgs.sort(key=lambda x: (x[0], x[1]))
        last = 0
        for tick, on, m, v in msgs:
            kind = "note_on" if on else "note_off"
            tr.append(mido.Message(kind, note=m, velocity=v, channel=ch, time=max(0, tick - last)))
            last = tick
        mid.tracks.append(tr)
    mid.save(path)
