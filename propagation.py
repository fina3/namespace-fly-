"""For each specific effect in comparison.json, how many synapses from the knocked-out cells?

Shortest path in the connectome from any silenced neuron to any neuron of the
affected cell type that fired in control, via connections with nonzero weight,
then the same restricted to connections from neurons that fired in control
(the only ones that can carry an effect in this model). Writes results/propagation.json.
"""
import json
from collections import deque
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def hops(ptr, post, sources, targets, allowed, limit=6):
    dist = {int(s): 0 for s in sources}
    queue = deque(sources)
    targets = set(int(t) for t in targets)
    while queue:
        i = queue.popleft()
        if dist[i] >= limit:
            continue
        if not allowed[i] and dist[i] > 0:
            continue
        for j in post[ptr[i]:ptr[i + 1]]:
            j = int(j)
            if j not in dist:
                dist[j] = dist[i] + 1
                if j in targets:
                    return dist[j]
                queue.append(j)
    return None


def main():
    root = Path('/workspaces/doomfly')
    g = np.load(root / 'outputs/doom/malecns_v1/graph.npz')
    keep = g['weight'] != 0
    ptr = np.r_[0, np.cumsum(np.add.reduceat(keep, g['ptr'][:-1]) * (np.diff(g['ptr']) > 0))].astype(np.int64)
    post = g['post'][keep]
    ids = g['ids']
    types = np.load(HERE / 'neuron_types.npz')['cell_type']
    comp = json.loads((HERE / 'results/comparison.json').read_text())
    conditions = json.loads((HERE / 'conditions.json').read_text())
    active = np.load(HERE / 'results/s1/control/neuron_counts.npz')['counts'] > 0
    everything = np.ones(len(ids), dtype=bool)
    out = {}
    for arm, r in comp['arms'].items():
        c = conditions[arm]
        silenced = np.flatnonzero(np.isin(types, c['silence']) | np.isin(ids, c.get('silence_ids', [])))
        out[arm] = {}
        for t in r['specific_cell_types']:
            tgt = np.flatnonzero((types == t['cell_type']) & active)
            out[arm][t['cell_type']] = {'hops_any_path': hops(ptr, post, silenced, tgt, everything),
                                        'hops_via_active_cells': hops(ptr, post, silenced, tgt, active),
                                        'active_cells_of_type': int(len(tgt))}
    (HERE / 'results/propagation.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
