"""Build demo/grid93-data.js: the first 10 s of every run in the 93-run experiment.

Everything comes from results/<stimulus>/<arm>/: per-tic decoded commands (ticks.csv)
and which Devbox ran it (summary.json). Nothing is synthesized.
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICS = 350   # 10 s at 35 tics per second
KIND = {'control': 'control', 'dnp20-off': 'knockout', 'dnpe017-off': 'knockout', 'both-off': 'knockout',
        'mevp9-off': 'knockout', 'blank-vision': 'vision', 'frozen-vision': 'vision'}
LABEL = {'control': 'INTACT', 'dnp20-off': 'DNp20 −', 'dnpe017-off': 'DNpe017 −', 'both-off': 'BOTH DNs −',
         'mevp9-off': 'MeVP9 −', 'blank-vision': 'BLANK SCREEN', 'frozen-vision': 'FROZEN FRAME'}


def digits(values, top):
    """Quantize to one character 0-9 per tic."""
    return ''.join(str(min(9, max(0, round(9 * v / top)))) for v in values)


def main():
    stimuli = json.loads((ROOT / 'stimuli.json').read_text())
    shams = json.loads((ROOT / 'shams.json').read_text())
    runs = []
    for stim in stimuli:
        for arm in list(KIND) + sorted(shams):
            d = ROOT / 'results' / stim / arm
            s = json.loads((d / 'summary.json').read_text())
            with open(d / 'ticks.csv') as f:
                t = list(csv.DictReader(f))[:TICS]
            b = s['behavior']
            runs.append({
                'stim': stim, 'arm': arm, 'kind': KIND.get(arm, 'sham'),
                'label': LABEL.get(arm, arm.upper().replace('-', ' ')),
                'cells': [n['id'] for n in s['intervention']['silenced_neurons']],
                'box': s['runtime']['host'],
                'turn': digits([abs(float(r['turn'])) for r in t], 4.0),
                'move': digits([float(r['forward']) for r in t], 20.0),
                'fire': ''.join(r['attack'] for r in t),
                # 120 s averages from the full run, for the tile's summary line
                'turn120': round(b['turn_mean_abs_deg_per_tic'], 2), 'move120': round(b['forward_mean'], 1),
                'fire120': round(100 * b['attack_frac']),
            })
    boxes = sorted({r['box'] for r in runs}, key=lambda b: (b != 'fly-control', b))
    data = {'tics': TICS, 'stimuli': stimuli, 'boxes': boxes, 'runs': runs,
            'counts': {k: sum(r['kind'] == k for r in runs) for k in ['control', 'knockout', 'sham', 'vision']}}
    (ROOT / 'demo/grid93-data.js').write_text('const GRID = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    print(len(runs), 'runs |', data['counts'], '|', {b: sum(r['box'] == b for r in runs) for b in boxes})


if __name__ == '__main__':
    main()
