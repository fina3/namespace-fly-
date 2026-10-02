"""Shared core for every experiment: load the DOOMFLY brain and silence neurons.

Silencing = every synapse onto and out of the target cells is set to weight 0.
A target that receives external current (photoreceptor, lamina, sugar cell) would
keep firing regardless, so those are refused rather than half-silenced.
"""
import json
import sys
from pathlib import Path

import numpy as np


def load(doomfly):
    """Return (brain, manifest, kernel build record) for a prepared DOOMFLY checkout."""
    if str(doomfly) not in sys.path:
        sys.path.insert(0, str(doomfly))
    from doom.native import NativeBrain, BUILD
    root = Path(doomfly)
    manifest = json.loads((root / 'outputs/doom/malecns_v1/manifest.json').read_text())
    brain = NativeBrain(root / 'outputs/doom/malecns_v1/graph.npz')
    return brain, manifest, BUILD


def indices_of(brain, neuron_ids):
    """Graph indices for connectome body IDs. Raises if an ID is not in the graph."""
    out = []
    for i in neuron_ids:
        hit = np.flatnonzero(brain.ids == int(i))
        if len(hit) != 1:
            raise ValueError(f'neuron id {i} not found in the graph')
        out.append(int(hit[0]))
    return out


def externally_driven(brain):
    return np.r_[brain.retina, brain.lamina, brain.sugar]


def silence(brain, target_indices):
    """Zero all synapses into and out of the targets. Returns (targets, rows_in, rows_out)."""
    targets = np.asarray(sorted(set(int(t) for t in target_indices)), dtype=np.int32)
    if np.isin(targets, externally_driven(brain)).any():
        raise RuntimeError('A target receives external current; zeroing synapses would not silence it')
    incoming = np.isin(brain.post, targets)
    outgoing = np.zeros(len(brain.post), dtype=bool)
    for i in targets:
        outgoing[brain.ptr[i]:brain.ptr[i + 1]] = True
    brain.weight[incoming | outgoing] = 0
    return targets, int(incoming.sum()), int(outgoing.sum())
