"""Compare the four arms against control. Refuses to run if stimuli differ."""
import csv, json, sys
from pathlib import Path
import numpy as np

RESULTS = Path(__file__).resolve().parent / 'results'
ARMS = ['control', 'dnp20-off', 'dnpe017-off', 'both-off']
DECODER = ['DNp20_R_10059', 'DNp20_L_10162', 'DNpe017_L_10527', 'DNpe017_R_555871']


def load(arm):
    d = RESULTS / arm
    with open(d / 'ticks.csv') as f:
        ticks = list(csv.DictReader(f))
    return {'summary': json.loads((d / 'summary.json').read_text()),
            'types': json.loads((d / 'celltype_spikes.json').read_text()),
            'counts': np.load(d / 'neuron_counts.npz'),
            'ticks': ticks}


def pct(x, base):
    return float('nan') if base == 0 else 100 * (x - base) / base


def main():
    arms = {a: load(a) for a in ARMS if (RESULTS / a / 'summary.json').exists()}
    if 'control' not in arms:
        sys.exit('control arm missing')
    ctl = arms['control']

    # 1. Same stimulus, or the comparison is meaningless.
    hashes = {a: r['summary']['stimulus_sha256'] for a, r in arms.items()}
    frames = {a: [t['frame_sha16'] for t in r['ticks']] for a, r in arms.items()}
    if len(set(hashes.values())) != 1 or any(f != frames['control'] for f in frames.values()):
        sys.exit(f'STIMULUS MISMATCH across arms: {hashes}')

    lines = ['# Results: DOOMFLY descending-neuron suppression', '',
             ctl['summary']['window'], '',
             f"Identical stimulus in all {len(arms)} arms: sha256 `{hashes['control']}` "
             f"({len(ctl['ticks'])} frames, every per-frame hash matches).", '',
             '## Decoded behavior (post warm-up)', '',
             '| Arm | mean abs turn (deg/tic) | turning tics | mean forward | forward tics | attack tics |',
             '|---|---|---|---|---|---|']
    out = {'stimulus_sha256': hashes['control'], 'arms': {}}
    for a, r in arms.items():
        b = r['summary']['behavior']
        lines.append(f"| {a} | {b['turn_mean_abs_deg_per_tic']:.3f} | {100*b['turn_nonzero_frac']:.1f}% | "
                     f"{b['forward_mean']:.3f} | {100*b['forward_nonzero_frac']:.1f}% | {100*b['attack_frac']:.1f}% |")
        out['arms'][a] = {'behavior': b}

    lines += ['', '## Decoder neuron firing rates (Hz)', '',
              '| Arm | ' + ' | '.join(DECODER) + ' |', '|---|' + '---|' * len(DECODER)]
    for a, r in arms.items():
        rates = r['summary']['readout_rates_hz']
        lines.append(f'| {a} | ' + ' | '.join(f'{rates[n]:.2f}' for n in DECODER) + ' |')
        out['arms'][a]['decoder_rates_hz'] = {n: rates[n] for n in DECODER}

    # 2. Off-target effects: what else in the 166k-neuron network changed?
    lines += ['', '## Rest of the network vs control', '',
              '| Arm | total spikes Δ | neurons with changed spike count | first diverging tic | mean rate (Hz) |',
              '|---|---|---|---|---|']
    c0 = ctl['counts']['counts']
    ctl_totals = [int(t['total_spikes']) for t in ctl['ticks']]
    for a, r in arms.items():
        c = r['counts']['counts']
        assert (r['counts']['ids'] == ctl['counts']['ids']).all()
        totals = [int(t['total_spikes']) for t in r['ticks']]
        first = next((i + 1 for i, (x, y) in enumerate(zip(totals, ctl_totals)) if x != y), None)
        net = r['summary']['network']
        changed = int((c != c0).sum())
        lines.append(f"| {a} | {pct(c.sum(), c0.sum()):+.3f}% | {changed:,} of {len(c):,} | "
                     f"{first if first else 'never'} | {net['mean_rate_hz']:.4f} |")
        out['arms'][a]['network'] = {'total_spikes': int(c.sum()), 'total_spikes_pct_vs_control': pct(c.sum(), c0.sum()),
                                     'neurons_changed': changed, 'first_diverging_tick': first}

    for a, r in arms.items():
        if a == 'control':
            continue
        silenced = set(r['summary']['intervention']['silenced_types'])
        deltas = []
        for t, v in r['types'].items():
            base = ctl['types'].get(t)
            if base is None or t in silenced:
                continue
            d = v['mean_rate_hz'] - base['mean_rate_hz']
            if d:
                deltas.append((abs(d), t, base['mean_rate_hz'], v['mean_rate_hz'], v['neurons']))
        deltas.sort(reverse=True)
        out['arms'][a]['top_celltype_changes'] = [
            {'cell_type': t, 'control_hz': b, 'arm_hz': x, 'neurons': n} for _, t, b, x, n in deltas[:15]]
        lines += ['', f'### {a}: cell types with the largest rate change (silenced types excluded)', '']
        if not deltas:
            lines.append('No cell type outside the silenced set changed rate.')
            continue
        lines += ['| Cell type | neurons | control Hz | arm Hz | Δ Hz |', '|---|---|---|---|---|']
        lines += [f'| {t} | {n} | {b:.3f} | {x:.3f} | {x-b:+.3f} |' for _, t, b, x, n in deltas[:15]]

    (RESULTS / 'comparison.md').write_text('\n'.join(lines) + '\n')
    (RESULTS / 'comparison.json').write_text(json.dumps(out, indent=2) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
