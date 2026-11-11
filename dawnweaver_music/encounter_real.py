"""Battle-encounter stingers with recorded instruments (VSCO 2 CE, CC0).

normal: ~2.3 s, A minor (leads into the A-minor violin battle)
boss:   ~4.8 s, C minor (leads into the C-minor boss battle)

Run:  python encounter_real.py [normal] [boss]
"""
import os
import sys
import numpy as np
import pyloudnorm
from synth import SR, midi_of, write_midi
from sampler import Instrument, StereoMix, place_swell
from songs import OUT, export
from orchestral_real import Orchestra, fit, mixdown
from ambient_real import extra

rng = np.random.default_rng(41)
N = midi_of


def finish(mx, gains, wet, seconds, name, title, target_lufs=-11.5, ir_decay=0.6):
    x = mixdown(mx, gains, wet, tail_s=seconds, ir_decay=ir_decay, drive=1.15)
    lufs = pyloudnorm.Meter(SR).integrated_loudness(x.T)
    x = x * 10 ** ((target_lufs - lufs) / 20)
    if np.max(np.abs(x)) > 0.89:
        x = x / np.max(np.abs(x)) * 0.89
    export(name, x, None, title)


def hit(mx, o, beat, chord_notes, bass_note, vel=1.0, crash=True):
    """Short tutti stab: horns/trombones/trumpets staccato + low strings + tuba + drums."""
    for m in chord_notes:
        mx.add("brass", o.hn_stac.render(fit(o.hn_stac, m - 12), None, vel), beat, pan=-0.3)
        mx.add("brass", o.tb_stac.render(fit(o.tb_stac, m - 12), None, vel), beat, pan=0.3)
        mx.add("brass", o.tp_stac.render(fit(o.tp_stac, m), None, vel * 0.9), beat, pan=0.1)
        mx.add("strings", o.vs_spic.render(fit(o.vs_spic, m), None, vel), beat, pan=-0.45)
    mx.add("low", o.vc_spic.render(fit(o.vc_spic, bass_note + 12), None, vel), beat, pan=0.35)
    mx.add("low", o.cb_spic.render(fit(o.cb_spic, bass_note), None, vel), beat, pan=0.4)
    mx.add("low", o.tu_stac.render(fit(o.tu_stac, bass_note), None, vel * 0.9), beat, pan=0.15)
    mx.add("perc", o.bdrum.render(vel=vel), beat)
    if crash:
        mx.add("perc", o.crash.render(vel=vel), beat, pan=0.4)
        mx.add("perc", o.crash.render(vel=vel * 0.85), beat, pan=-0.4)


# =====================================================================
# Normal encounter: string swoosh up -> "ta-ta-TAN" tutti in A minor
# =====================================================================
def normal(o):
    bpm = 168
    spb = 60 / bpm
    seconds = 2.4
    mx = StereoMix(seconds + 3.0, bpm, align_onsets=True)
    # beat 0-1: rising harmonic-minor run in 32nds (violins + violas an octave down)
    run = ["A4", "B4", "C5", "D5", "E5", "F5", "G#5", "A5"]
    run_ev = []
    for i, n in enumerate(run):
        b = i * 0.125
        v = 0.55 + 0.05 * i
        mx.add("strings", o.vs_spic.render(fit(o.vs_spic, N(n)), None, v), b, pan=-0.4)
        mx.add("strings", o.va_spic.render(fit(o.va_spic, N(n) - 12), None, v * 0.9), b, pan=0.2)
        run_ev.append((b, 0.125, N(n)))
    # snare roll + timpani roll crescendo under the run
    sr_ = o.snare_roll.render(vel=0.8)
    n = int(1.0 * spb * SR)
    mx.add("perc", sr_[:, :n] * np.linspace(0.25, 1.0, n), 0, pan=0.1, align=False)
    mx.add("timp", o.timp_roll.render(N("E2"), spb, 0.7, release=0.03, fade_in=0.15), 0, pan=-0.2)
    # hits: E (dominant) on the "and", then A minor
    am = [N("A4"), N("C5"), N("E5")]
    e7 = [N("G#4"), N("B4"), N("E5")]
    hit(mx, o, 1.0, am, N("A1") + 12, vel=0.85, crash=False)
    hit(mx, o, 1.5, e7, N("E2"), vel=0.8, crash=False)
    hit(mx, o, 2.0, am, N("A1") + 12, vel=1.0, crash=True)
    for b, r in ((1.0, "A2"), (1.5, "E2"), (2.0, "A2")):
        mx.add("timp", o.timp.render(N(r), 1.2, 0.9, release=0.4), b, pan=-0.2)
    # held A-minor chord ringing out after the last hit (strings + horns)
    for m in am:
        mx.add("pad", o.vs_sus.render(fit(o.vs_sus, m), 1.1, 0.6, release=0.6), 2.0, pan=-0.35)
        mx.add("pad", o.hn_sus.render(fit(o.hn_sus, m - 12), 1.0, 0.55, release=0.6), 2.0, pan=-0.2)
    mx.add("pad", o.vc_sus.render(fit(o.vc_sus, N("A2")), 1.1, 0.6, release=0.6), 2.0, pan=0.35)

    finish(mx, {"strings": 0.8, "brass": 1.0, "low": 0.7, "perc": 0.65, "timp": 0.75, "pad": 0.6},
           {"strings": 0.2, "brass": 0.25, "low": 0.12, "perc": 0.2, "timp": 0.25, "pad": 0.35},
           seconds, "dawnweaver_encounter_normal", "戦闘突入（通常）")
    write_midi(os.path.join(OUT, "dawnweaver_encounter_normal.mid"), bpm,
               [("Run", 48, 0, run_ev),
                ("Hits", 61, 1, [(b, 0.4, m) for b, ch in ((1.0, am), (1.5, e7), (2.0, am)) for m in ch])])


# =====================================================================
# Boss encounter: gong + tremolo swell -> Db -> C minor brass, C minor
# =====================================================================
def boss(o):
    bpm = 120
    spb = 60 / bpm
    seconds = 4.8
    mx = StereoMix(seconds + 3.5, bpm, align_onsets=True)
    # beat 0: low boom (gong + bass drum + low C on contrabass/tuba)
    mx.add("perc", o.gong.render(vel=0.75), 0, pan=0.2)
    mx.add("perc", o.bdrum.render(vel=1.0), 0)
    mx.add("low", o.tu_sus.render(fit(o.tu_sus, N("C2")), 1.0 * spb, 0.6, release=0.6), 0, pan=0.15)
    mx.add("low", o.cb_sus.render(fit(o.cb_sus, N("C2")), 2.5 * spb, 0.45, release=0.5), 0, pan=0.4)
    mx.add("timp", o.timp.render(N("C3"), 1.5, 1.0, release=0.5), 0, pan=-0.2)
    # beats 0.5-3: string tremolo crescendo on a C / Db / G cluster rising in tension
    trem = [("vs_trem", N("G4"), -0.4), ("vs_trem", N("Ab4"), -0.3), ("va_trem", N("C4"), 0.1),
            ("va_trem", N("Db4"), 0.2), ("vc_trem", N("C3"), 0.35)]
    n = int(2.5 * spb * SR)
    cresc = np.linspace(0.15, 1.0, n) ** 1.6
    for attr, m, pan in trem:
        inst = getattr(o, attr)
        sig = inst.render(fit(inst, m), 2.5 * spb, 0.8, release=0.05)[:, :n]
        mx.add("trem", sig * cresc[: sig.shape[1]], 0.5, pan=pan, align=False)
    mx.add("timp", o.timp_roll.render(N("G2"), 2.4 * spb, 0.85, release=0.03, fade_in=1.0), 0.6, pan=-0.2)
    place_swell(mx, "perc", o.swell.render(vel=0.8), 3.0)
    # beat 3: Db major stab ("da-"), beat 3.5: C minor ("DAAN") held
    db = [N("Db5"), N("F5"), N("Ab5")]
    cm = [N("C5"), N("Eb5"), N("G5")]
    hit(mx, o, 3.0, db, N("Db2"), vel=0.9, crash=False)
    mx.add("timp", o.timp.render(N("Db3"), 1.0, 0.9, release=0.3), 3.0, pan=-0.2)
    hit(mx, o, 3.5, cm, N("C2"), vel=1.0, crash=True)
    mx.add("perc", o.gong.render(vel=0.8), 3.5, pan=-0.2)
    mx.add("timp", o.timp.render(N("C3"), 2.0, 1.0, release=0.8), 3.5, pan=-0.2)
    # C minor held by low brass and strings, decaying into the battle
    for m in cm:
        mx.add("pad", o.tb_sus.render(fit(o.tb_sus, m - 12), 1.6, 0.8, release=0.8), 3.5, pan=0.3)
        mx.add("pad", o.hn_sus.render(fit(o.hn_sus, m - 12), 1.6, 0.75, release=0.8), 3.5, pan=-0.3)
        mx.add("pad", o.vs_sus.render(fit(o.vs_sus, m), 1.6, 0.6, release=0.8), 3.5, pan=-0.4)
    mx.add("pad", o.tu_sus.render(fit(o.tu_sus, N("C2")), 1.6, 0.8, release=0.8), 3.5, pan=0.15)

    finish(mx, {"trem": 1.8, "brass": 1.0, "strings": 0.6, "low": 0.75, "perc": 0.7, "timp": 0.8, "pad": 0.7},
           {"trem": 0.3, "brass": 0.3, "strings": 0.2, "low": 0.2, "perc": 0.3, "timp": 0.3, "pad": 0.4},
           seconds, "dawnweaver_encounter_boss", "戦闘突入（ボス）", ir_decay=0.75)
    write_midi(os.path.join(OUT, "dawnweaver_encounter_boss.mid"), bpm,
               [("Tremolo", 44, 0, [(0.5, 2.5, m) for _, m, _ in trem]),
                ("Brass", 61, 1, [(3.0, 0.5, m) for m in db] + [(3.5, 1.5, m) for m in cm]),
                ("Low", 58, 2, [(0, 2, N("C2")), (3.0, 0.5, N("Db2")), (3.5, 1.5, N("C2"))])])


if __name__ == "__main__":
    which = sys.argv[1:] or ["normal", "boss"]
    orch = extra(Orchestra())
    orch.va_trem = Instrument("Strings/Viola Section/trem")
    if "normal" in which:
        normal(orch)
    if "boss" in which:
        boss(orch)
