"""'糸車の剣舞' re-orchestrated with real recorded strings (VSCO 2 CE, CC0).

Run:  python violin_real.py     -> out/dawnweaver_battle_violin_real_loop.(wav|mp3|ogg)
"""
import os
import numpy as np
from synth import SR, midi_of, parse_line, make_ir, reverb, fold_loop, write_midi, hp, lp
from sampler import Instrument, StereoMix, place_swell, onset_latency
from songs import OUT, chord, export
from songs2 import root_in, run
from harmony import harmony_under

rng = np.random.default_rng(11)

BPM, NBARS = 168, 24
SPB = 60 / BPM
LOOP_S = NBARS * 4 * SPB

PROG = ["Am", "F", "G", "Am", "Am", "F", "G", "E",
        "Dm", "G", "C", "Am", "Dm", "F", "E", "E",
        "Am", "G", "F", "E", "Am", "G", "F", "E7"]


def melody():
    mel = parse_line(" ".join([
        "E5:.5 A5:.5 B5:.5 C6:.5 B5:.5 A5:.5 E5:1", "F5:.5 A5:.5 C6:1 B5:.5 A5:.5 F5:1",
        "G5:.5 B5:.5 D6:1 C6:.5 B5:.5 G5:1", "A5:2.5 C6:.5 B5:.5 A5:.5",
        "E6:1 D6:.5 C6:.5 B5:.5 A5:.5 C6:1", "D6:1 C6:.5 A5:.5 F5:1 A5:1",
        "B5:.5 C6:.5 D6:.5 B5:.5 G5:1 D5:1", "E5:.25 F5:.25 G#5:.25 A5:.25 B5:.5 G#5:.5 E5:2",
        "F5:1.5 A5:.5 D6:2", "D6:.5 C6:.5 B5:.5 A5:.5 G5:2", "E5:.5 G5:.5 C6:1.5 B5:.5 C6:1", "A5:3 r:1",
        "F5:.5 A5:.5 D6:1 F6:1.5 E6:.5", "D6:1 C6:.5 A5:.5 F5:2", "E5:.5 G#5:.5 B5:.5 D6:.5 E6:2",
        "E6:.25 D6:.25 C6:.25 B5:.25 A5:.25 G#5:.25 F5:.25 E5:.25 D5:.5 E5:.5 G#5:1",
    ]))
    mel += run("A5 C6 E6 C6 A5 C6 E6 A6", 64) + parse_line("G6:.5 E6:.5 A6:1", 66)
    mel += run("G5 B5 D6 B5 G5 B5 D6 G6", 68) + parse_line("F6:.5 D6:.5 G6:1", 70)
    mel += run("F5 A5 C6 A5 F5 A5 C6 F6", 72) + parse_line("E6:.5 C6:.5 F6:1", 74)
    mel += parse_line("E6:1 D6:.5 C6:.5 B5:1 G#5:1 "
                      "A6:1.5 E6:.5 C6:1 A5:1 B5:1.5 D6:.5 G6:2 A6:1 G6:.5 F6:.5 E6:1 C6:1", 76)
    mel += run("B5 C6 B5 A5 G#5 A5 B5 D6", 92) + parse_line("E6:.5 D6:.5 B5:.5 G#5:.5", 94)
    return mel


def phrase_vel(beat):
    """Dynamics: A mf, B a bit softer then swelling, C forte."""
    bar = beat / 4
    if bar < 8:
        return 0.72 + 0.03 * (bar % 4)
    if bar < 16:
        return 0.62 + 0.035 * (bar - 8)
    return 0.92


def main():
    vln_arco = Instrument("Strings/Solo Violin/Arco Vib")
    vs_sus = Instrument("Strings/Violin Section/susVib")
    vs_spic = Instrument("Strings/Violin Section/Spic")
    va_sus = Instrument("Strings/Viola Section/susvib")
    va_spic = Instrument("Strings/Viola Section/spic")
    vc_sus = Instrument("Strings/Cello Section/susvib")
    vc_spic = Instrument("Strings/Cello Section/spic")
    cb_spic = Instrument("Strings/Solo Contrabass/Spic")
    harp = Instrument("Strings/Harp")
    timp = Instrument("Percussion/Timpani", pattern=r"^Timpani1_Hit", pitched=False)
    timp.pitched = True
    for s in timp.samples:
        s["midi"] = 41.4  # measured fundamental of drum 1 (~89.5 Hz)
    bdrum = Instrument("Percussion", pattern=r"^BDrumNewhit", pitched=False)
    snare = Instrument("Percussion", pattern=r"^Snare2-HitSN", pitched=False)
    crash = Instrument("Percussion", pattern=r"^cymbal-crash1_(mf|ff)", pitched=False)
    tamb = Instrument("Percussion", pattern=r"^Tamb1-Hit", pitched=False)
    swell = Instrument("Percussion", pattern=r"^susCymb1-cresc-Median", pitched=False)

    mx = StereoMix(LOOP_S + 5.0, BPM, align_onsets=True)
    H = 0.006  # timing humanize (s)

    # ---- solo violin lead, phrased like a player: notes inside a phrase are slurred (start on
    # the sustain part of the arco sample and cross-fade with the previous note); a new bow
    # (soft attack) only after a rest or on a long note that starts on the beat.
    mel = melody()
    nxt = {round(b, 3): i for i, (b, d, m) in enumerate(mel)}
    # cross-fade length at each joint (shared by the outgoing and incoming note)
    xf_after = []
    for i, (b, d, m) in enumerate(mel):
        j = nxt.get(round(b + d, 3))
        xf_after.append(min(0.03, 0.35 * d * SPB, 0.35 * mel[j][1] * SPB) if j is not None else 0.0)
    xf_before = [0.0] * len(mel)
    for i, (b, d, m) in enumerate(mel):
        j = nxt.get(round(b + d, 3))
        if j is not None:
            xf_before[j] = xf_after[i]
    rendered = []
    for i, (b, d, m) in enumerate(mel):
        v = phrase_vel(b) * rng.uniform(0.97, 1.02)
        nd = d * SPB
        xin, xout = xf_before[i], xf_after[i]
        connected, joins_next = xin > 0, xout > 0
        new_bow = (not connected) or (d >= 1 and abs(b - round(b)) < 1e-6)
        lead = xin / 2
        length = lead + nd + (xout / 2 if joins_next else 0.0)
        rel = 0.002 if joins_next else 0.10
        lat = 0.0
        if not connected:
            # phrase start: measure how long the bowed attack takes to speak, start that much
            # earlier and extend the note by the same amount so the joint with the next note stays put
            sig = vln_arco.render(m, length + 0.25, v, release=0.002)
            lat = onset_latency(sig)
            e = min(sig.shape[1], int((lat + length) * SR))
            if not joins_next:
                r = min(sig.shape[1] - e, int(0.10 * SR))
                sig = sig[:, :e + r].copy()
                sig[:, e:e + r] *= np.linspace(1, 0, r) ** 1.5
            else:
                sig = sig[:, :e].copy()
            lead = lat
            length = lat + length
        elif new_bow:   # re-bow: light attack
            sig = vln_arco.render(m, length, v * 0.97, release=rel, offset=0.035)
        else:           # slur: start on the sustain
            sig = vln_arco.render(m, length, v * 0.95, release=rel, offset=0.14)
        if connected:   # equal-power fade-in across the shared joint
            n = min(sig.shape[1], int(xin * SR))
            sig[:, :n] *= np.sin(np.linspace(0, np.pi / 2, n))
        if joins_next:  # equal-power fade-out across the joint
            n = int(xout * SR)
            e = min(sig.shape[1], int(length * SR))
            sig = sig[:, :e]
            sig[:, e - n:e] *= np.cos(np.linspace(0, np.pi / 2, n))
        # measure the note body (between the joints) for level matching below
        a, z = int((lead + 0.1 * nd) * SR), int((lead + 0.9 * nd) * SR)
        body = np.sqrt(np.mean(sig[:, a:max(z, a + 64)] ** 2)) + 1e-12
        rendered.append((b - lead / SPB, sig, v, body, m, length))  # lead = joint half or onset latency
    # level-match: the per-pitch recordings differ by several dB, which made neighbouring notes
    # jump in level. Scale every note so its body level follows the phrase dynamics (v),
    # limited to +-6 dB so the natural shape of each recording is kept.
    c = np.median([r[3] / r[2] for r in rendered])
    for beat, sig, v, body, m, length in rendered:
        g = np.clip(c * v / body, 0.5, 2.0)
        mx.add("solo", sig, beat, pan=0.05, gain=g, note=(m, length), align=False)  # aligned above

    # B section: violin section plays a 3rd/6th under the solo
    duet = harmony_under([e for e in mel if 32 <= e[0] < 64 and e[1] >= 0.5], PROG)
    for b, d, m in duet:
        mx.add("sect", vs_sus.render(m, d * SPB + 0.05, 0.45, release=0.18), b, pan=-0.35, humanize=H, rng=rng)
    # C section: violin section doubles the long melody notes an octave down for weight
    for b, d, m in mel:
        if b >= 64 and d >= 1:
            mx.add("sect", vs_sus.render(m - 12, d * SPB + 0.05, 0.55, release=0.2), b, pan=-0.3, humanize=H, rng=rng)

    bass_ev, stacc_ev, pad_ev, harp_ev = [], [], [], []
    for bi, c in enumerate(PROG):
        b0 = bi * 4
        r = root_in(c, "E2")
        loud = 0.85 if bi >= 16 else 0.7
        # cellos: spiccato 8ths; contrabass on beats 1 & 3 an octave down
        for k in range(8):
            m = r + (12 if k in (2, 6) else 0)
            mx.add("low", vc_spic.render(m, None, loud * (1.0 if k % 2 == 0 else 0.8)), b0 + k * 0.5,
                   pan=0.3, humanize=H, rng=rng)
            bass_ev.append((b0 + k * 0.5, 0.4, m))
        for k in (0, 2):
            mx.add("low", cb_spic.render(r - 12 if r - 12 >= 28 else r, None, loud), b0 + k, pan=0.35,
                   humanize=H, rng=rng)
        # upper strings: off-beat spiccato chords (all 8ths in C)
        tones = chord(c, 4)[1][:3]
        for k in range(8):
            if k % 2 == 1 or bi >= 16:
                v = 0.6 if k % 2 else 0.45
                mx.add("stacc", vs_spic.render(tones[2], None, v), b0 + k * 0.5, pan=-0.45, humanize=H, rng=rng)
                mx.add("stacc", va_spic.render(tones[0], None, v), b0 + k * 0.5, pan=0.15, humanize=H, rng=rng)
                for m in (tones[0], tones[2]):
                    stacc_ev.append((b0 + k * 0.5, 0.25, m))
        # sustained bed (soft): violas + cellos, violins join in C
        ptones = chord(c, 3)[1]
        mx.add("pad", va_sus.render(ptones[1] + (12 if ptones[1] < 52 else 0), 4 * SPB, 0.35, release=0.35),
               b0, pan=0.2, rng=rng)
        mx.add("pad", vc_sus.render(ptones[0], 4 * SPB, 0.35, release=0.35), b0, pan=0.35, rng=rng)
        if bi >= 16:
            mx.add("pad", vs_sus.render(ptones[2] + 12, 4 * SPB, 0.3, release=0.35), b0, pan=-0.4, rng=rng)
        for m in ptones:
            pad_ev.append((b0, 4, m))
        # harp: 8th arpeggios in B, rising arpeggio on each bar of A's 4th/8th bars
        if 8 <= bi < 16:
            a = chord(c, 4)[1][:3]
            for k in range(8):
                m = [a[0], a[1], a[2], a[0] + 12][k % 4] + (12 if k >= 4 else 0)
                mx.add("harp", harp.render(m, None, 0.55), b0 + k * 0.5, pan=0.5, humanize=H, rng=rng)
                harp_ev.append((b0 + k * 0.5, 0.5, m))

    # ---- orchestral percussion
    for bi in range(NBARS):
        b0 = bi * 4
        c_sec = bi >= 16
        mx.add("perc", bdrum.render(vel=0.9 if c_sec else 0.75), b0, pan=0.0)
        if c_sec or bi % 2:
            mx.add("perc", bdrum.render(vel=0.6), b0 + 2, pan=0.0)
        for k in (1, 3):
            mx.add("perc", snare.render(vel=0.55 if c_sec else 0.4), b0 + k, pan=0.1, humanize=H, rng=rng)
        if c_sec:
            for k in range(8):
                mx.add("perc", tamb.render(vel=0.5 if k % 2 else 0.3), b0 + k * 0.5, pan=-0.25, humanize=H, rng=rng)
        if bi in (0, 8, 16):
            mx.add("perc", crash.render(vel=0.8), b0, pan=0.4)
        if bi % 8 == 7:
            for k in range(4):
                mx.add("perc", snare.render(vel=0.35 + 0.15 * k), b0 + 3 + k * 0.25, pan=0.1)
        if bi == 15:
            place_swell(mx, "perc", swell.render(vel=0.6), 16 * 4)
        # timpani on phrase starts and cadences (F2..C3 to keep the pitch-shift small)
        r = root_in(PROG[bi], "F2")
        if bi % 4 == 0 or bi % 8 == 7:
            mx.add("timp", timp.render(r, 1.6, 0.85, release=0.4), b0, pan=-0.15)
        if bi % 8 == 7:
            for k in range(6):
                mx.add("timp", timp.render(r, 0.3, 0.35 + 0.08 * k, release=0.1), b0 + 2 + k * 0.25, pan=-0.15)

    # ---- mix
    gains = {"solo": 0.8, "sect": 0.95, "low": 0.55, "stacc": 0.45, "pad": 0.75, "harp": 0.75,
             "perc": 0.5, "timp": 0.8}
    wet = {"solo": 0.22, "sect": 0.25, "low": 0.12, "stacc": 0.15, "pad": 0.3, "harp": 0.3,
           "perc": 0.12, "timp": 0.2}
    ir = make_ir(seconds=2.2, decay=0.5)
    total = None
    for name, b in mx.buses.items():
        sig = reverb(b * gains[name], wet[name], ir)
        total = sig if total is None else total + sig
    loop_n = int(round(LOOP_S * SR))
    x = fold_loop(total, loop_n)
    x = hp(x, 30, 2)
    x = x / np.max(np.abs(x))
    x = np.tanh(x * 1.15) / np.tanh(1.15)  # gentle peak control only
    x = x / np.max(np.abs(x)) * 0.89
    # keep the loudness the game's playback gain was tuned for (v1.8: -11.5 LUFS)
    import pyloudnorm
    lufs = pyloudnorm.Meter(SR).integrated_loudness(x.T)
    if lufs > -11.5:
        x = x * 10 ** ((-11.5 - lufs) / 20)
    export("dawnweaver_battle_violin_real_loop", x, loop_n, "糸車の剣舞 (Violin Battle, recorded strings)")
    write_midi(os.path.join(OUT, "dawnweaver_battle_violin_real.mid"), BPM,
               [("Solo Violin", 40, 0, mel), ("Violin Section", 48, 1, duet), ("Cello/Bass", 42, 2, bass_ev),
                ("Staccato Strings", 45, 3, stacc_ev), ("Pad", 48, 4, pad_ev), ("Harp", 46, 5, harp_ev)])


if __name__ == "__main__":
    main()
