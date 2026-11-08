"""Sample-based renderer using VSCO 2 Community Edition (CC0) recordings.

Sample note labels in VSCO 2 CE are not always at concert pitch (several string
sections are labelled an octave low), so every sample's pitch is measured and the
label is snapped to the nearest matching octave before use.
"""
import os
import re
import json
import warnings
import numpy as np
from scipy.io import wavfile
from synth import SR, midi_of, hz

warnings.filterwarnings("ignore", category=wavfile.WavFileWarning)

VSCO = os.environ.get("VSCO_DIR", "/home/user/sgossner/vsco-2-ce")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vsco_pitch_cache.json")
NOTE_RE = re.compile(r"_([A-G]#?)(-?\d)(?=_|\.wav)")


def _load(path):
    sr, d = wavfile.read(path)
    scale = {np.dtype("int16"): 32768.0, np.dtype("int32"): 2147483648.0}.get(d.dtype, 1.0)
    d = d.astype(np.float64) / scale
    if d.ndim == 1:
        d = np.stack([d, d], 1)
    d = d[:, :2].T
    if sr != SR:
        n = int(d.shape[1] * SR / sr)
        x = np.linspace(0, d.shape[1] - 1, n)
        d = np.stack([np.interp(x, np.arange(d.shape[1]), c) for c in d])
    return d


def _onset(d, thresh=0.06):
    m = np.abs(d).max(0)
    pk = m.max() + 1e-12
    idx = int(np.argmax(m > pk * thresh))
    return max(0, idx - int(0.004 * SR))


def _detect_midi(d, start):
    """Autocorrelation pitch estimate on a steady part of the note."""
    seg = d.mean(0)[start + int(0.12 * SR): start + int(0.45 * SR)]
    if len(seg) < 4096:
        seg = d.mean(0)[start: start + 8192]
    seg = seg - seg.mean()
    seg = seg * np.hanning(len(seg))
    n = 1 << (len(seg) * 2 - 1).bit_length()
    spec = np.fft.rfft(seg, n)
    ac = np.fft.irfft(np.abs(spec) ** 2)[: len(seg)]
    lo, hi = int(SR / 2200), int(SR / 30)
    lag = lo + int(np.argmax(ac[lo:hi]))
    # prefer the shortest lag with a strong peak (avoid octave-down errors)
    best = lag
    for div in (2, 3, 4):
        cand = int(round(lag / div))
        if cand >= lo:
            w = ac[max(lo, cand - 2): cand + 3]
            if w.max() > 0.85 * ac[lag]:
                best = max(lo, cand - 2) + int(np.argmax(w))
    return 69 + 12 * np.log2(SR / best / 440.0)


class Instrument:
    def __init__(self, folder, pattern=None, pitched=True, label_fix=True, gain=1.0, force_fix=None):
        self.folder = os.path.join(VSCO, folder)
        self.pitched = pitched
        self.gain = gain
        files = sorted(f for f in os.listdir(self.folder) if f.endswith(".wav")
                       and (pattern is None or re.search(pattern, f)))
        cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
        self.samples = []  # dicts: midi, layer, path
        offsets = []
        for f in files:
            path = os.path.join(self.folder, f)
            layer = 0
            mv = re.search(r"_v(\d)", f)
            if mv:
                layer = int(mv.group(1))
            elif re.search(r"_(f|mf|ff)\.wav$", f):
                layer = 2
            elif re.search(r"_(p|pp|mp)\.wav$", f):
                layer = 1
            midi = None
            if pitched:
                m = NOTE_RE.search(f)
                if not m:
                    continue
                label = midi_of(m.group(1) + m.group(2))
                key = os.path.relpath(path, VSCO)
                if key not in cache:
                    d = _load(path)
                    cache[key] = float(_detect_midi(d, _onset(d)))
                midi = label
                offsets.append(12 * round((cache[key] - label) / 12))
            self.samples.append({"midi": midi, "layer": layer, "path": path})
        json.dump(cache, open(CACHE, "w"), indent=0, sort_keys=True)
        if pitched and label_fix and offsets:
            # one octave correction per folder (majority vote; robust to detector outliers)
            vals, counts = np.unique(offsets, return_counts=True)
            self.octave_fix = int(vals[np.argmax(counts)]) if force_fix is None else force_fix
            for smp in self.samples:
                smp["midi"] += self.octave_fix
                # a few samples are mislabelled by about a semitone (e.g. clarinet "F#5" sounds F):
                # correct those when the measured offset is clearly between 1 and 1.6 semitones
                r = (cache[os.path.relpath(smp["path"], VSCO)] - smp["midi"] + 6) % 12 - 6
                if 1.0 <= abs(r) <= 1.6:
                    smp["midi"] += int(round(r))
        self.layers = sorted({s["layer"] for s in self.samples})
        self._cache = {}
        self._rr = {}

    def _get(self, path):
        if path not in self._cache:
            d = _load(path)
            st = _onset(d)
            d = d[:, st:]
            # level-normalise on the loudest 50 ms frame within the first 1.5 s, so slow bowed
            # attacks are not over-boosted and the natural attack shape is kept
            seg = d[:, : int(1.5 * SR)].mean(0)
            fr = int(0.05 * SR)
            nf = max(1, len(seg) // fr)
            frames = seg[: nf * fr].reshape(nf, fr) if len(seg) >= fr else seg[None, :]
            ref = np.sqrt((frames ** 2).mean(1)).max() + 1e-9
            self._cache[path] = d / ref * 0.1
        return self._cache[path]

    def pick(self, midi, vel):
        layer = self.layers[min(len(self.layers) - 1, int(vel * len(self.layers)))] if self.layers else 0
        cands = [s for s in self.samples if s["layer"] == layer] or self.samples
        if self.pitched:
            dist = min(abs(s["midi"] - midi) for s in cands)
            cands = [s for s in cands if abs(s["midi"] - midi) == dist]
        k = (midi, layer)
        i = self._rr.get(k, 0)
        self._rr[k] = i + 1
        return cands[i % len(cands)]

    def render(self, midi=60, dur=None, vel=0.8, release=0.12, fade_in=0.0, offset=0.0):
        """offset: seconds to skip into the (pitch-shifted) sample, e.g. to start a slurred
        note on the sustain part instead of a fresh attack."""
        s = self.pick(midi, vel)
        d = self._get(s["path"])
        ratio = 2 ** ((midi - s["midi"]) / 12) if self.pitched and s["midi"] != midi else 1.0
        start = int(offset * SR * ratio)
        if start:
            d = d[:, start:]
        if ratio != 1.0:
            n = int(d.shape[1] / ratio)
            if dur is not None:
                n = min(n, int((dur + release) * SR) + 1)
            x = np.arange(n) * ratio
            d = np.stack([np.interp(x, np.arange(d.shape[1]), c) for c in d])
        if dur is not None:
            n = min(d.shape[1], int((dur + release) * SR))
            d = d[:, :n].copy()
            hold = min(n, int(dur * SR))
            rel = n - hold
            if rel > 0:
                d[:, hold:] *= np.linspace(1, 0, rel) ** 1.5
        else:
            d = d.copy()
        if fade_in > 0:
            fi = min(d.shape[1], int(fade_in * SR))
            d[:, :fi] *= np.linspace(0, 1, fi)
        tail = min(d.shape[1], int(0.01 * SR))
        d[:, -tail:] *= np.linspace(1, 0, tail)
        return d * vel * self.gain


def onset_latency(sig, frac=0.5, max_s=0.2):
    """Seconds from the start of a rendered note until it is perceptibly 'there': the 5 ms
    envelope first reaches `frac` of the note's early steady level. Slow bowed attacks can take
    50-180 ms, plucks and spiccato ~0-10 ms."""
    m = np.abs(sig).max(0)
    w = int(0.005 * SR)
    if len(m) < 4 * w:
        return 0.0
    env = np.convolve(m, np.ones(w) / w, mode="same")
    if len(env) > int(0.4 * SR):
        level = min(np.median(env[int(0.1 * SR):int(0.4 * SR)]), env.max())
    else:
        level = env.max()
    if level <= 0:
        return 0.0
    return min(max_s, int(np.argmax(env >= frac * level)) / SR)


class StereoMix:
    """Like synth.Mix but for stereo sample buffers."""

    def __init__(self, seconds, bpm, align_onsets=False):
        self.spb = 60.0 / bpm
        self.n = int(seconds * SR)
        self.buses = {}
        # when True, every added note is moved earlier by its measured onset latency so that
        # slow-attack (bowed) and fast-attack (plucked) parts land together on the beat
        self.align_onsets = align_onsets

    def add(self, bus, sig, beat, pan=0.0, gain=1.0, humanize=0.0, rng=None, note=None, align=None):
        b = self.buses.setdefault(bus, np.zeros((2, self.n)))
        t = beat * self.spb + (rng.normal(0, humanize) if humanize and rng is not None else 0.0)
        if (self.align_onsets if align is None else align):
            t -= onset_latency(sig)
        i = max(0, int(round(t * SR)))
        if i >= self.n:
            return
        sig = sig[:, : self.n - i] * gain
        if sig.shape[0] == 1:
            sig = np.vstack([sig, sig])
        l = np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
        r = np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
        # balance-style pan (keeps the recording's own stereo image)
        b[0, i:i + sig.shape[1]] += sig[0] * min(1.0, l)
        b[1, i:i + sig.shape[1]] += sig[1] * min(1.0, r)


def place_swell(mx, bus, sig, target_beat, pan=0.0, gain=1.0, tail_s=0.6):
    """Place a crescendo sample so its loudest point lands on target_beat; trim the ring-out."""
    env = np.abs(sig).max(0)
    w = int(0.03 * SR)
    sm = np.convolve(env, np.ones(w) / w, mode="same")
    pk = int(np.argmax(sm))
    end = min(sig.shape[1], pk + int(tail_s * SR))
    s = sig[:, :end].copy()
    fade = end - pk
    if fade > 0:
        s[:, pk:end] *= np.linspace(1, 0, fade) ** 2
    mx.add(bus, s, target_beat - pk / SR / mx.spb, pan=pan, gain=gain, align=False)
