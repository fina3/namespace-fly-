"""Integrity checks on every result set. Exits non-zero on any problem."""
import csv, glob, json, os, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    stimuli = json.loads((HERE / 'stimuli.json').read_text())
    conditions = json.loads((HERE / 'conditions.json').read_text()) | json.loads((HERE / 'shams.json').read_text())
    types = np.load(HERE / 'neuron_types.npz')
    ids = types['ids']
    problems, provenance, runs = [], set(), 0
    for stim, cfg in stimuli.items():
        ctl = json.loads((HERE / f'results/{stim}/control/summary.json').read_text())
        for d in sorted(glob.glob(str(HERE / f'results/{stim}/*/'))):
            arm = os.path.basename(d.rstrip('/'))
            runs += 1
            s = json.loads(Path(d, 'summary.json').read_text())
            c = np.load(Path(d, 'neuron_counts.npz'))
            with open(Path(d, 'ticks.csv')) as f:
                rows = list(csv.DictReader(f))
            p = s['provenance']
            provenance.add((p['doomfly_commit'], p['kernel']['binary_sha256'], p['kernel']['kernel_source_sha256'],
                            json.dumps(p['source_hashes'], sort_keys=True)))
            want = set(conditions[arm].get('silence_ids', [])) | {
                int(i) for i, t in zip(ids, types['cell_type']) if t in conditions[arm]['silence']}
            got = {int(n['id']) for n in s['intervention']['silenced_neurons']}
            n_ticks = int(round(s['config']['seconds'] * 35))
            warmup = int(round(s['config']['warmup'] * 35))
            checks = {
                'condition and tag': s['condition'] == arm == s['tag'],
                'stimulus config': s['config']['seed'] == cfg['seed'] and s['config']['sweep_deg_per_tic'] == cfg['sweep'],
                'same duration as control': s['config'] == ctl['config'],
                'tick count and order': [int(r['tick']) for r in rows] == list(range(1, n_ticks + 1)),
                'frames match control': s['stimulus_sha256'] == ctl['stimulus_sha256'],
                'neuron order': bool((c['ids'] == ids).all()),
                'spike totals agree': int(c['counts'].sum()) == s['network']['total_spikes']
                                      == sum(int(r['total_spikes']) for r in rows[warmup:]),
                'outputs finite': all(np.isfinite([float(r['turn']), float(r['forward'])]).all() for r in rows),
                'silenced set': want == got,
                'silenced cells at zero': int(c['counts'][np.isin(ids, list(got))].sum()) == 0,
                'vision mode': s['intervention']['vision'] == conditions[arm].get('vision', 'live'),
            }
            problems += [f'{stim}/{arm}: {k}' for k, ok in checks.items() if not ok]
    if len(provenance) != 1:
        problems.append(f'{len(provenance)} different code/data/kernel versions across runs')
    expected = len(stimuli) * len(conditions)
    if runs != expected:
        problems.append(f'{runs} runs found, {expected} expected')
    print(f'{runs} runs checked, {len(problems)} problems')
    for p in problems:
        print('  ' + p)
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
