"""Build demo/science-data.js from a provisioned experiment: every arm's effect on every measure,
per stimulus, so the page can draw the sham cloud against the targeted knockouts and apply the rule.

  python3 demo/build_science.py experiments/knockouts-100
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'experiments/knockouts-100')
TARGETS = {'dnp20-off': 'DNp20 −', 'dnpe017-off': 'DNpe017 −', 'both-off': 'both DNs −', 'mevp9-off': 'MeVP9 −'}
BEHAVIOR = [('turn_mean_abs_deg_per_tic', 'TURN', '°/tic'), ('forward_mean', 'MOVE', 'u/tic'), ('attack_frac', 'FIRE', 'frac. of tics')]
TYPES = [('DNp20', 'DNp20 rate'), ('DNpe017', 'DNpe017 rate'), ('w-cHIN', 'w-cHIN rate'), ('PS278', 'PS278 rate'), ('MeVP9', 'MeVP9 rate')]


def main():
    stimuli = json.loads((EXP / 'stimuli.json').read_text())
    shams = sorted(json.loads((EXP / 'shams.json').read_text()))
    types = np.load(EXP / 'neuron_types.npz')
    cell_type = types['cell_type']
    arms = list(TARGETS) + shams
    measures = [{'key': k, 'label': l, 'unit': u, 'kind': 'behavior'} for k, l, u in BEHAVIOR] + \
               [{'key': t, 'label': l, 'unit': 'Hz', 'kind': 'rate'} for t, l in TYPES]
    delta = {m['key']: {s: {} for s in stimuli} for m in measures}
    control = {}
    for s in stimuli:
        def summary(arm): return json.loads((EXP / 'results' / s / arm / 'summary.json').read_text())
        def counts(arm): return np.load(EXP / 'results' / s / arm / 'neuron_counts.npz')['counts']
        def silenced(arm): return [int(n['id']) for n in summary(arm)['intervention']['silenced_neurons']]
        c0, b0 = counts('control'), summary('control')['behavior']
        window = summary('control')['config']['seconds'] - summary('control')['config']['warmup']
        control[s] = {k: b0[k] for k, _, _ in BEHAVIOR}
        for arm in arms:
            b, c, sil = summary(arm)['behavior'], counts(arm), silenced(arm)
            keep = ~np.isin(types['ids'], sil)
            for k, _, _ in BEHAVIOR:
                delta[k][s][arm] = round(b[k] - b0[k], 5)
            for t, _ in TYPES:
                m = (cell_type == t) & keep
                control[s][t] = round(float(c0[m].sum() / m.sum() / window), 4) if m.any() else None
                delta[t][s][arm] = round(float((c[m].sum() - c0[m].sum()) / m.sum() / window), 5) if m.any() else None

    # the rule, applied exactly as compare.py does: |Δ| larger than every sham's |Δ|, same sign, every stimulus
    verdict = {}
    for arm in TARGETS:
        verdict[arm] = {}
        for m in measures:
            signs = []
            for s in stimuli:
                v = delta[m['key']][s][arm]
                top = max(abs(delta[m['key']][s][x]) for x in shams)
                signs.append((1 if v > 0 else -1) if v is not None and abs(v) > top else 0)
            verdict[arm][m['key']] = bool(signs[0]) and all(x == signs[0] for x in signs)

    data = {'experiment': EXP.name, 'stimuli': stimuli, 'shams': shams, 'targets': TARGETS, 'measures': measures,
            'control': control, 'delta': delta, 'verdict': verdict,
            'cells': {arm: json.loads((EXP / 'results' / list(stimuli)[0] / arm / 'summary.json').read_text())['intervention']['silenced_neurons'] for arm in TARGETS}}
    (ROOT / 'demo/science-data.js').write_text('const SCI = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    for arm in TARGETS:
        print(f"{arm:12s} specific: {[m['label'] for m in measures if verdict[arm][m['key']]]}")


if __name__ == '__main__':
    main()
