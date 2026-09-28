"""One arm of the DOOMFLY suppression experiment, open loop.

Every arm sees the same Doom frames: ViZDoom with a fixed seed, driven by a
scripted camera sweep that never reads the brain. The fly brain only watches;
its decoded turn/forward/attack commands are recorded, not applied. Differences
between arms can therefore come only from the silenced neurons.

Silencing = every synapse onto (and out of) the target cells is zeroed. DNs get
no external current in DOOMFLY, so they sit at rest (-52 mV < -45 mV threshold)
and cannot spike. The run asserts that they never do.
"""
import argparse, csv, hashlib, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--condition', required=True)
    p.add_argument('--doomfly', default='/workspaces/doomfly')
    p.add_argument('--seconds', type=float, default=20.0, help='game/neural seconds to simulate')
    p.add_argument('--warmup', type=float, default=1.0, help='seconds excluded from summary metrics')
    p.add_argument('--seed', type=int, default=41027, help='ViZDoom seed (DOOMFLY default)')
    p.add_argument('--sweep', type=float, default=2.0, help='scripted camera turn, degrees per tic')
    p.add_argument('--out', default=str(HERE / 'results'))
    p.add_argument('--tag', help='output directory name (default: the condition name)')
    args = p.parse_args()

    conditions = json.loads((HERE / 'conditions.json').read_text())
    if args.condition not in conditions:
        p.error(f'unknown condition; choose from {list(conditions)}')
    silence = conditions[args.condition]['silence']
    silence_ids = conditions[args.condition].get('silence_ids', [])
    vision = conditions[args.condition].get('vision', 'live')
    tag = args.tag or args.condition

    sys.path.insert(0, args.doomfly)
    from doom.native import NativeBrain, BUILD
    from doom.engine import NeuralControls
    from doom.game import Game, retinal_samples
    import pyarrow.feather as feather

    root = Path(args.doomfly)
    manifest = json.loads((root / 'outputs/doom/malecns_v1/manifest.json').read_text())
    readouts = manifest['readouts']
    brain = NativeBrain(root / 'outputs/doom/malecns_v1/graph.npz')
    nodes = feather.read_table(root / 'connectome_data/malecns_v1/normalized/neurons.feather',
                               columns=['cell_type', 'superclass']).to_pandas()
    assert len(nodes) == brain.n

    # --- intervention -------------------------------------------------------
    by_id = [int(np.flatnonzero(brain.ids == i)[0]) for i in silence_ids]  # IndexError if an id is absent
    targets = np.asarray(sorted({r['index'] for r in readouts if r['type'] in silence} | set(by_id)), dtype=np.int32)
    missing = set(silence) - {r['type'] for r in readouts}
    if missing:
        raise RuntimeError(f'No readout neurons of type {missing} in manifest')
    externally_driven = np.r_[brain.retina, brain.lamina, brain.sugar]
    if np.isin(targets, externally_driven).any():
        raise RuntimeError('A target receives external current; zeroing synapses would not silence it')
    incoming = np.isin(brain.post, targets)
    outgoing = np.zeros(len(brain.post), dtype=bool)
    for i in targets:
        outgoing[brain.ptr[i]:brain.ptr[i + 1]] = True
    brain.weight[incoming | outgoing] = 0
    intervention = {
        'silenced_types': silence,
        'silenced_neurons': [{'id': str(brain.ids[i]), 'type': str(nodes.cell_type.iloc[i])} for i in targets],
        'vision': vision,
        'incoming_synapse_rows_zeroed': int(incoming.sum()),
        'outgoing_synapse_rows_zeroed': int(outgoing.sum()),
        'method': 'All incoming and outgoing edge weights of target neurons set to 0; no other change.',
    }
    print(json.dumps({'condition': args.condition, 'tag': tag, **intervention}), flush=True)

    # --- run ---------------------------------------------------------------
    controls = NeuralControls(readouts, mode='bci')
    game = Game(seed=args.seed, scenario='combat_survival', spectator=False)
    scripted = {'turn': args.sweep, 'forward': 0.0, 'attack': False}
    total_tics = int(round(args.seconds * 35))
    warmup_tics = int(round(args.warmup * 35))
    names = [f"{r['type']}_{r['side']}_{r['id']}" for r in readouts]

    out = Path(args.out) / tag
    frozen = None
    out.mkdir(parents=True, exist_ok=True)
    stim_hash = hashlib.sha256()
    window_counts = np.zeros(brain.n, dtype=np.int64)
    window_ms = 0.0
    rows = []
    wall_start = time.perf_counter()
    for tick in range(1, total_tics + 1):
        if game.observation()['finished']:
            game.new_episode()
        frame = game.pixels()
        stim_hash.update(frame.tobytes())
        light = retinal_samples(frame, brain.uv)
        # Vision controls: the game still runs and frames are still hashed.
        if vision == 'blank':
            light.fill(0)
        elif vision == 'frozen':
            if frozen is None:
                frozen = light.copy()
            light = frozen
        steps = int(round(tick * 10000 / 35)) - brain.cursor  # 285/286 substeps keep clocks aligned
        counts, _ = brain.step(light, steps * .1)
        action = controls.decode(counts, steps * .1 / 1000)
        game.act(scripted)  # the brain never moves the camera
        rows.append([tick, game.episode, hashlib.sha256(frame.tobytes()).hexdigest()[:16],
                     round(action['turn'], 6), round(action['forward'], 6), int(action['attack']),
                     int(counts.sum())] + [int(counts[r['index']]) for r in readouts])
        if tick > warmup_tics:
            window_counts += counts
            window_ms += steps * .1
        if tick % 35 == 0:
            el = time.perf_counter() - wall_start
            print(f'{tag} t={tick/35:.0f}s/{args.seconds:.0f}s wall={el:.0f}s '
                  f'speed={brain.sim_ms/1000/el:.3f}x', flush=True)
    wall = time.perf_counter() - wall_start
    game.close()

    if len(targets) and window_counts[targets].sum() != 0:
        raise RuntimeError('Silenced neurons spiked; intervention failed')

    # --- outputs -----------------------------------------------------------
    header = ['tick', 'episode', 'frame_sha16', 'turn', 'forward', 'attack', 'total_spikes'] + names
    with open(out / 'ticks.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    np.savez_compressed(out / 'neuron_counts.npz', ids=brain.ids, counts=window_counts)

    window_s = window_ms / 1000
    def grouped(labels):
        labels = labels.fillna('unassigned').astype(str).to_numpy()
        keys, inv = np.unique(labels, return_inverse=True)
        spikes = np.bincount(inv, weights=window_counts, minlength=len(keys))
        sizes = np.bincount(inv, minlength=len(keys))
        return {k: {'neurons': int(n), 'spikes': int(s), 'mean_rate_hz': float(s / n / window_s)}
                for k, n, s in zip(keys, sizes, spikes)}
    (out / 'celltype_spikes.json').write_text(json.dumps(grouped(nodes.cell_type), separators=(',', ':')))

    post = np.asarray(rows[warmup_tics:], dtype=object)
    turn = post[:, 3].astype(float); fwd = post[:, 4].astype(float); atk = post[:, 5].astype(int)
    commit = subprocess.run(['git', '-C', args.doomfly, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    summary = {
        'condition': args.condition,
        'tag': tag,
        'question': conditions[args.condition]['question'],
        'window': (f'Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed {args.seed}, '
                   f'{args.sweep} deg/tic scripted sweep), measuring decoded commands over '
                   f'{window_s:.3f} s of neural time starting at t={args.warmup:.3f} s '
                   f'(first {warmup_tics} tics are warm-up and excluded).'),
        'intervention': intervention,
        'stimulus_sha256': stim_hash.hexdigest(),
        'config': {'seconds': args.seconds, 'warmup': args.warmup, 'seed': args.seed, 'sweep_deg_per_tic': args.sweep,
                   'decoder': 'bci', 'scenario': 'combat_survival', 'loop': 'open (commands decoded, not applied)'},
        'provenance': {'doomfly_commit': commit, 'kernel': BUILD, 'source_hashes': manifest['source_hashes']},
        'behavior': {
            'turn_mean_abs_deg_per_tic': float(np.abs(turn).mean()),
            'turn_mean_signed_deg_per_tic': float(turn.mean()),
            'turn_nonzero_frac': float((np.abs(turn) > 1e-6).mean()),
            'forward_mean': float(fwd.mean()),
            'forward_nonzero_frac': float((fwd > 1e-6).mean()),
            'attack_frac': float(atk.mean()),
        },
        'readout_rates_hz': {n: float(window_counts[r['index']] / window_s) for n, r in zip(names, readouts)},
        'network': {'total_spikes': int(window_counts.sum()),
                    'mean_rate_hz': float(window_counts.sum() / brain.n / window_s),
                    'active_neurons': int((window_counts > 0).sum()),
                    'superclass': grouped(nodes.superclass)},
        'runtime': {'wall_seconds': round(wall, 1), 'speed_x_realtime': round(brain.sim_ms / 1000 / wall, 4),
                    'host': os.uname().nodename},
    }
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'done': tag, **summary['behavior'], 'wall_s': round(wall, 1)}), flush=True)


if __name__ == '__main__':
    main()
