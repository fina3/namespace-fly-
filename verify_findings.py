"""Checks behind the headline findings, from saved results only (no Devbox needed)."""
import csv, json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
T = np.load(HERE / 'neuron_types.npz')
ids, ct, sc = T['ids'], T['cell_type'], T['superclass']
shams = sorted(json.loads((HERE / 'shams.json').read_text()))


def counts(s, a):
    return np.load(HERE / f'results/{s}/{a}/neuron_counts.npz')['counts'].astype(np.int64)


def summary(s, a):
    return json.loads((HERE / f'results/{s}/{a}/summary.json').read_text())


def turns(s, a):
    with open(HERE / f'results/{s}/{a}/ticks.csv') as f:
        return np.array([float(r['turn']) for r in csv.DictReader(f)][35:])


def ix(i):
    return int(np.flatnonzero(ids == i)[0])


for s in ['s1', 's2', 's3']:
    c0 = counts(s, 'control')
    print(f'== {s}')

    # 1. Decoder neurons as relays of MeVP9 12764 / 12356
    mismatch, active_mevp9 = 0, set()
    for a in ['control', 'dnpe017-off', 'blank-vision', 'frozen-vision'] + shams:
        c = counts(s, a)
        active_mevp9 |= set(ids[(ct == 'MeVP9') & (c > 0)].tolist())
        mismatch = max(mismatch, abs(c[ix(10059)] - c[ix(12764)]), abs(c[ix(10162)] - c[ix(12356)]),
                       abs(c[ix(10527)] - c[ix(12356)]))
    print(f"1. MeVP9 cells: {(ct == 'MeVP9').sum()}, ever active: {sorted(active_mevp9)}; "
          f'largest spike-count gap between a decoder cell and its MeVP9 cell over 28 arms: {mismatch}')
    print(f'   DNpe017_R {c0[ix(555871)]} vs MeVP9 12764 {c0[ix(12764)]} / 12356 {c0[ix(12356)]}')

    # 2. Turning direction with live, blank and frozen vision
    for a in ['control', 'blank-vision', 'frozen-vision']:
        t = turns(s, a)
        print(f'2. {a}: right on {100 * (t > 0).mean():.2f}% of tics, left on {100 * (t < 0).mean():.2f}%')

    # 3. Which cells outside the visual system fire at all
    visual = np.char.startswith(sc, 'ol_') | np.char.startswith(sc, 'visual')
    outside = sorted(((str(ct[i]), int(c0[i])) for i in np.flatnonzero((c0 > 0) & ~visual)), key=lambda x: -x[1])
    print(f'3. active neurons: {(c0 > 0).sum()}; active outside the visual system: {len(outside)} -> {outside}')

    # 4. Turning change with DNpe017 off, against shams
    t0 = summary(s, 'control')['behavior']['turn_mean_abs_deg_per_tic']
    d = summary(s, 'dnpe017-off')['behavior']['turn_mean_abs_deg_per_tic'] - t0
    v = [summary(s, a)['behavior']['turn_mean_abs_deg_per_tic'] - t0 for a in shams]
    print(f'4. turning change, DNpe017 off: {d:+.4f}; shams with a larger change: '
          f'{sum(abs(x) > abs(d) for x in v)} of {len(v)}')

    # 5. Double knockout vs sum of single knockouts
    both, pred = counts(s, 'both-off'), counts(s, 'dnp20-off') + counts(s, 'dnpe017-off') - c0
    print(f'5. neurons where both-off differs from the sum of singles: '
          f'{[(int(ids[i]), str(ct[i])) for i in np.flatnonzero(both != pred)]}')

    # 6. w-cHIN
    w = ct == 'w-cHIN'
    print(f'6. w-cHIN spikes per active cell in control: {c0[w][c0[w] > 0].tolist()}; '
          f"DNpe017 off: {counts(s, 'dnpe017-off')[w].sum()}; lowest sham: {min(counts(s, a)[w].sum() for a in shams)}")
