"""Compare every arm against its control. Refuses to run if stimuli differ.

Arms are grouped by stimulus. Sham knockouts measure how much ANY two-neuron
knockout perturbs the network, which is the yardstick for off-target effects.
"""
import csv, json, sys
from pathlib import Path
import numpy as np

RESULTS = Path(__file__).resolve().parent / 'results'
GROUPS = {  # control arm -> arms sharing its stimulus
    'control': ['control-rep', 'dnp20-off', 'dnpe017-off', 'both-off', 'mevp9-off',
                'sham-a', 'sham-b', 'sham-c', 'blank-vision', 'frozen-vision'],
    'control-s2': ['dnp20-off-s2', 'dnpe017-off-s2'],
}
DECODER = ['DNp20_R_10059', 'DNp20_L_10162', 'DNpe017_L_10527', 'DNpe017_R_555871']
WATCH = ['DNp20', 'DNpe017', 'w-cHIN', 'MeVP9']


def load(arm):
    d = RESULTS / arm
    if not (d / 'summary.json').exists():
        return None
    with open(d / 'ticks.csv') as f:
        ticks = list(csv.DictReader(f))
    return {'summary': json.loads((d / 'summary.json').read_text()),
            'types': json.loads((d / 'celltype_spikes.json').read_text()),
            'counts': np.load(d / 'neuron_counts.npz'),
            'ticks': ticks}


def pct(x, base):
    return float('nan') if base == 0 else 100 * (x - base) / base


def main():
    lines = ['# Results: DOOMFLY descending-neuron suppression', '']
    out = {}
    for control, members in GROUPS.items():
        ctl = load(control)
        if ctl is None:
            if control == 'control':
                sys.exit('control arm missing')
            continue
        arms = {control: ctl} | {a: r for a in members if (r := load(a)) is not None}

        # Same stimulus, or the comparison is meaningless.
        frames = [t['frame_sha16'] for t in ctl['ticks']]
        for a, r in arms.items():
            if (r['summary']['stimulus_sha256'] != ctl['summary']['stimulus_sha256']
                    or [t['frame_sha16'] for t in r['ticks']] != frames):
                sys.exit(f'STIMULUS MISMATCH: {a} vs {control}')

        cfg = ctl['summary']['config']
        lines += [f"## Stimulus: seed {cfg['seed']}, sweep {cfg['sweep_deg_per_tic']} deg/tic", '',
                  ctl['summary']['window'], '',
                  f"Identical game frames in all {len(arms)} arms: sha256 `{ctl['summary']['stimulus_sha256']}` "
                  f"({len(frames)} frames, {len(set(frames))} distinct, every per-frame hash matches). "
                  'In the blank and frozen arms the game frames are the same but the receptors are fed black / the first frame.', '',
                  '### Decoded behavior', '',
                  '| Arm | silenced | mean abs turn (deg/tic) | Δ turn vs control | mean forward | attack tics |',
                  '|---|---|---|---|---|---|']
        b0 = ctl['summary']['behavior']
        for a, r in arms.items():
            b = r['summary']['behavior']
            sil = ', '.join(f"{n['type']} {n['id']}" for n in r['summary']['intervention']['silenced_neurons']) or '—'
            lines.append(f"| {a} | {sil} | {b['turn_mean_abs_deg_per_tic']:.4f} | "
                         f"{pct(b['turn_mean_abs_deg_per_tic'], b0['turn_mean_abs_deg_per_tic']):+.2f}% | "
                         f"{b['forward_mean']:.3f} | {100*b['attack_frac']:.1f}% |")
            out[a] = {'control': control, 'behavior': b}

        lines += ['', '### Decoder neuron firing rates (Hz)', '',
                  '| Arm | ' + ' | '.join(DECODER) + ' |', '|---|' + '---|' * len(DECODER)]
        for a, r in arms.items():
            rates = r['summary']['readout_rates_hz']
            lines.append(f'| {a} | ' + ' | '.join(f'{rates[n]:.2f}' for n in DECODER) + ' |')
            out[a]['decoder_rates_hz'] = {n: rates[n] for n in DECODER}

        # Off-target effects, excluding the silenced neurons themselves.
        lines += ['', '### Rest of the network vs control (silenced neurons excluded)', '',
                  '| Arm | other neurons with changed spike count | sum of abs spike changes | total spikes Δ | '
                  + ' | '.join(f'{t} spikes' for t in WATCH) + ' |', '|---|---|---|---|' + '---|' * len(WATCH)]
        ids, c0 = ctl['counts']['ids'], ctl['counts']['counts']
        for a, r in arms.items():
            c = r['counts']['counts']
            assert (r['counts']['ids'] == ids).all()
            silenced = [int(n['id']) for n in r['summary']['intervention']['silenced_neurons']]
            other = (c != c0) & ~np.isin(ids, silenced)
            lines.append(f"| {a} | {int(other.sum()):,} | {int(np.abs(c - c0)[other].sum()):,} | "
                         f"{pct(c.sum(), c0.sum()):+.3f}% | "
                         + ' | '.join(str(r['types'][t]['spikes']) for t in WATCH) + ' |')
            out[a]['network'] = {'other_neurons_changed': int(other.sum()),
                                 'sum_abs_spike_change': int(np.abs(c - c0)[other].sum()),
                                 'total_spikes_pct_vs_control': pct(c.sum(), c0.sum()),
                                 'watch_spikes': {t: r['types'][t]['spikes'] for t in WATCH}}
        lines.append('')

    lines += ['## Where the activity is (control)', '', '| Superclass | neurons | mean rate (Hz) |', '|---|---|---|']
    sc = load('control')['summary']['network']['superclass']
    for k, v in sorted(sc.items(), key=lambda x: -x[1]['spikes']):
        if v['spikes']:
            lines.append(f"| {k} | {v['neurons']:,} | {v['mean_rate_hz']:.3f} |")
    silent = sum(v['neurons'] for v in sc.values() if not v['spikes'])
    lines.append(f'| all other superclasses | {silent:,} | 0 (no spikes at all) |')

    (RESULTS / 'comparison.md').write_text('\n'.join(lines) + '\n')
    (RESULTS / 'comparison.json').write_text(json.dumps(out, indent=2) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
