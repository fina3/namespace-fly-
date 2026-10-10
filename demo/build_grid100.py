"""Build demo/grid100-data.js: the first 10 s of every run in the 100-run, one-run-per-Devbox experiment.

Everything comes from experiments/knockouts-100-1perbox/results/<stimulus>/<arm>/: per-tic decoded
commands (ticks.csv) and which Devbox ran it (summary.json). Nothing is synthesized.

  python3 demo/build_grid100.py [experiments/knockouts-100-1perbox]
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'experiments/knockouts-100-1perbox'
TICS = 350   # 10 s at 35 tics per second
KIND = {'control': 'control', 'dnp20-off': 'knockout', 'dnpe017-off': 'knockout', 'both-off': 'knockout',
        'mevp9-off': 'knockout', 'blank-vision': 'vision', 'frozen-vision': 'vision'}
LABEL = {'control': 'INTACT', 'dnp20-off': 'DNp20 −', 'dnpe017-off': 'DNpe017 −', 'both-off': 'BOTH DNs −',
         'mevp9-off': 'MeVP9 −', 'blank-vision': 'BLANK SCREEN', 'frozen-vision': 'FROZEN FRAME'}


def digits(values, top):
    """Quantize to one character 0-9 per tic."""
    return ''.join(str(min(9, max(0, round(9 * v / top)))) for v in values)


def main():
    stimuli = json.loads((EXP / 'stimuli.json').read_text())
    shams = json.loads((EXP / 'shams.json').read_text())
    prov = {r['run']: r for r in json.loads((EXP / 'provenance.json').read_text())['runs']}
    runs = []
    for stim in stimuli:
        for arm in list(KIND) + sorted(shams):
            d = EXP / 'results' / stim / arm
            s = json.loads((d / 'summary.json').read_text())
            with open(d / 'ticks.csv') as f:
                t = list(csv.DictReader(f))[:TICS]
            b, p = s['behavior'], prov[f'{stim}/{arm}']
            runs.append({
                'stim': stim, 'arm': arm, 'kind': KIND.get(arm, 'sham'),
                'label': LABEL.get(arm, arm.upper().replace('-', ' ')),
                'box': s['runtime']['host'], 'box_id': p['id'], 'box_s': p['total_s'],
                'turn': digits([abs(float(r['turn'])) for r in t], 4.0),
                'move': digits([float(r['forward']) for r in t], 20.0),
                'fire': ''.join(r['attack'] for r in t),
                # 120 s averages from the full run, for the tile's lost/intact marks
                'turn120': round(b['turn_mean_abs_deg_per_tic'], 2), 'move120': round(b['forward_mean'], 1),
                'fire120': round(100 * b['attack_frac']),
            })
    assert len(runs) == 100 and len({r['box'] for r in runs}) == 100
    lost = lambda r: not (r['turn120'] and r['move120'] and r['fire120'])
    data = {'tics': TICS, 'stimuli': stimuli, 'runs': runs,
            'counts': {k: sum(r['kind'] == k for r in runs) for k in ['control', 'knockout', 'sham', 'vision']},
            'lost': {k: sum(lost(r) for r in runs if r['kind'] == k) for k in ['control', 'knockout', 'sham', 'vision']},
            'box_minutes_median': sorted(r['box_s'] for r in runs)[50] / 60}
    (ROOT / 'demo/grid100-data.js').write_text('const GRID = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    print(len(runs), 'runs on', len({r['box'] for r in runs}), 'Devboxes |', data['counts'], '| any output lost:', data['lost'])


if __name__ == '__main__':
    main()
