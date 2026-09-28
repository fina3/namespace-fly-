"""Pick sham knockout pairs by fixed rules and a fixed seed.

Writes shams.json, plus neuron_types.npz (cell-type labels) for compare.py.

A sham neuron must be comparable to the targets (active, similar output size)
but unrelated to the circuit under test:
  - fires 15-45 Hz in the stimulus-1 control run (targets fire 24-40 Hz)
  - 300-900 outgoing connection rows (DNpe017 has ~580, MeVP9 350-460)
  - receives no external current (not a photoreceptor, lamina or sugar cell)
  - not DNp20, DNpe017, MeVP9 or w-cHIN, and not directly presynaptic to any of them
Rules were fixed before any sham results were seen.
"""
import argparse, json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
WATCH = ['DNp20', 'DNpe017', 'MeVP9', 'w-cHIN']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--doomfly', default='/workspaces/doomfly')
    p.add_argument('--control-counts', required=True, help='neuron_counts.npz of the stimulus-1 control run')
    p.add_argument('--pairs', type=int, default=24)
    p.add_argument('--seed', type=int, default=20260927)
    args = p.parse_args()

    import pyarrow.feather as feather
    root = Path(args.doomfly)
    g = np.load(root / 'outputs/doom/malecns_v1/graph.npz')
    ptr, post, ids = g['ptr'], g['post'], g['ids']
    n = len(ids)
    pre = np.repeat(np.arange(n), np.diff(ptr))
    nodes = feather.read_table(root / 'connectome_data/malecns_v1/normalized/neurons.feather',
                               columns=['cell_type', 'superclass']).to_pandas()
    cell_type = nodes.cell_type.fillna('?').astype(str).to_numpy()
    superclass = nodes.superclass.fillna('?').astype(str).to_numpy()
    c = np.load(args.control_counts)
    assert (c['ids'] == ids).all()
    rate = c['counts'] / 119.0  # 120 s run minus 1 s warm-up

    watch = np.isin(cell_type, WATCH)
    presyn_to_watch = np.zeros(n, dtype=bool)
    presyn_to_watch[np.unique(pre[watch[post]])] = True
    external = np.zeros(n, dtype=bool)
    external[np.r_[g['retina'], g['lamina'], g['sugar']]] = True
    outdeg = np.diff(ptr)
    ok = (rate >= 15) & (rate <= 45) & (outdeg >= 300) & (outdeg <= 900) & ~external & ~watch & ~presyn_to_watch
    candidates = np.flatnonzero(ok)
    if len(candidates) < 2 * args.pairs:
        raise RuntimeError(f'only {len(candidates)} candidates for {args.pairs} pairs')

    picks = np.random.default_rng(args.seed).choice(candidates, size=2 * args.pairs, replace=False)
    shams = {}
    for k in range(args.pairs):
        a, b = picks[2 * k], picks[2 * k + 1]
        shams[f'sham-{k + 1:02d}'] = {
            'silence': [], 'silence_ids': [int(ids[a]), int(ids[b])],
            'question': f'Sham: {cell_type[a]} + {cell_type[b]} ({superclass[a]}, {superclass[b]}); '
                        f'{rate[a]:.1f} / {rate[b]:.1f} Hz in control.'}
    (HERE / 'shams.json').write_text(json.dumps(shams, indent=2) + '\n')
    # Cell-type labels for compare.py, which runs where the connectome is not downloaded.
    np.savez_compressed(HERE / 'neuron_types.npz', ids=ids, cell_type=cell_type.astype('U'), superclass=superclass.astype('U'))
    types = {}
    for i in picks:
        types[cell_type[i]] = types.get(cell_type[i], 0) + 1
    print(json.dumps({'candidates': int(len(candidates)), 'pairs': args.pairs, 'seed': args.seed,
                      'candidate_superclasses': {s: int((superclass[candidates] == s).sum())
                                                 for s in np.unique(superclass[candidates])},
                      'picked_types': types}))


if __name__ == '__main__':
    main()
