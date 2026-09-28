"""Compare every arm against its control and against the sham knockouts.

Layout: results/<stimulus>/<arm>/. Refuses to run if any arm's frames differ
from its control's.

The model is deterministic, so there is no noise to test against. The 24 sham
knockouts (random pairs of comparable neurons) are the null: they show how much
ANY two-neuron knockout moves each measure. An effect is called SPECIFIC only if,
in every stimulus, its size exceeds the largest size produced by any sham
(|arm delta| > max |sham delta|), with the same sign every time.

Why size and not "outside the sham range": every sham is an optic-lobe cell (the
only active cells that qualify), and shams shift some measures the same way every
time (all 24 raise Dm17, for example). An arm that merely fails to do that would
sit outside the range without having any effect of its own.
Cell-type screens test hundreds of types, so read single-type hits with that in mind.
"""
import csv, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
TARGETS = ['dnp20-off', 'dnpe017-off', 'both-off', 'mevp9-off']  # mevp9-off is the upstream follow-up
VISION = ['blank-vision', 'frozen-vision']
WATCH = ['DNp20', 'DNpe017', 'MeVP9', 'w-cHIN']
BEHAVIOR = [('turn_mean_abs_deg_per_tic', 'turn'), ('forward_mean', 'forward'), ('attack_frac', 'attack')]


def load(stim, arm):
    d = RESULTS / stim / arm
    if not (d / 'summary.json').exists():
        return None
    with open(d / 'ticks.csv') as f:
        frames = [row['frame_sha16'] for row in csv.DictReader(f)]
    c = np.load(d / 'neuron_counts.npz')
    return {'summary': json.loads((d / 'summary.json').read_text()), 'frames': frames,
            'ids': c['ids'], 'counts': c['counts'].astype(np.int64)}


def measures(r, ctl, type_index, n_types):
    """Everything compared against shams, for one arm on one stimulus."""
    s = r['summary']
    silenced = np.isin(r['ids'], [int(n['id']) for n in s['intervention']['silenced_neurons']])
    if r['counts'][silenced].any():
        sys.exit(f"silenced neurons spiked in {s['tag']}")
    window_s = s['config']['seconds'] - s['config']['warmup']
    delta = r['counts'] - ctl['counts']
    keep = ~silenced  # a knockout's own cells are excluded from every network measure
    type_delta = np.bincount(type_index[keep], weights=delta[keep], minlength=n_types)
    type_size = np.bincount(type_index[keep], minlength=n_types)
    b, b0 = s['behavior'], ctl['summary']['behavior']
    m = {f'{name}_delta': b[key] - b0[key] for key, name in BEHAVIOR}
    m['other_neurons_changed'] = int(((delta != 0) & keep).sum())
    m['sum_abs_spike_change'] = int(np.abs(delta[keep]).sum())
    return m, np.divide(type_delta, type_size * window_s, out=np.zeros(n_types), where=type_size > 0)


def main():
    stimuli = json.loads((HERE / 'stimuli.json').read_text())
    shams = sorted(json.loads((HERE / 'shams.json').read_text()))
    types = np.load(HERE / 'neuron_types.npz')
    type_names, type_index = np.unique(types['cell_type'], return_inverse=True)
    n_types = len(type_names)
    superclass_of = {}
    for t, sc in zip(types['cell_type'], types['superclass']):
        superclass_of.setdefault(t, sc)

    data = {}  # stim -> arm -> {'measures', 'type_delta', 'summary'}
    for stim in stimuli:
        ctl = load(stim, 'control')
        if ctl is None:
            sys.exit(f'{stim}/control missing')
        if not (ctl['ids'] == types['ids']).all():
            sys.exit('neuron order differs from neuron_types.npz')
        data[stim] = {}
        for arm in ['control'] + TARGETS + VISION + shams:
            r = load(stim, arm)
            if r is None:
                sys.exit(f'{stim}/{arm} missing')
            if r['summary']['stimulus_sha256'] != ctl['summary']['stimulus_sha256'] or r['frames'] != ctl['frames']:
                sys.exit(f'STIMULUS MISMATCH: {stim}/{arm}')
            m, td = measures(r, ctl, type_index, n_types)
            data[stim][arm] = {'measures': m, 'type_delta': td, 'summary': r['summary']}

    def sham_range(stim, key):
        v = [data[stim][s]['measures'][key] for s in shams]
        return min(v), max(v)

    def sham_max_abs(stim, key):
        return max(abs(data[stim][s]['measures'][key]) for s in shams)

    def beyond(stim, arm, key):  # sign of the effect if its size beats every sham, else 0
        v = data[stim][arm]['measures'][key]
        return (1 if v > 0 else -1) if abs(v) > sham_max_abs(stim, key) else 0

    lines = ['# Results: DOOMFLY knockout experiment', '',
             f'{len(stimuli)} stimuli × ({len(TARGETS)} target knockouts + {len(shams)} sham knockouts + control '
             f'+ {len(VISION)} vision controls) = {len(stimuli) * (1 + len(TARGETS) + len(shams) + len(VISION))} runs, '
             f"120 s each. Frame hashes match within every stimulus.", '',
             '**Specific** = larger in size than the largest effect of any of the 24 shams, same direction, '
             'in every stimulus.', '']
    for stim, cfg in stimuli.items():
        ctl = data[stim]['control']['summary']
        lines.append(f"- **{stim}**: seed {cfg['seed']}, sweep {cfg['sweep']}°/tic, {len(set(load(stim, 'control')['frames']))} "
                     f"distinct frames, sha256 `{ctl['stimulus_sha256'][:16]}…`. {ctl['window']}")
    out = {'stimuli': stimuli, 'shams': shams, 'arms': {}}

    # 1. Behavior and network-size measures, per stimulus, against the sham range.
    keys = [f'{n}_delta' for _, n in BEHAVIOR] + ['other_neurons_changed', 'sum_abs_spike_change']
    fmt = {'turn_delta': '{:+.4f}', 'forward_delta': '{:+.3f}', 'attack_delta': '{:+.3f}',
           'other_neurons_changed': '{:,}', 'sum_abs_spike_change': '{:,}'}
    lines += ['', '## Decoded behavior and network change vs control', '',
              'Δ turn in deg/tic, Δ forward in decoder units, Δ attack as a fraction of tics. '
              'Network columns exclude the knocked-out cells themselves.', '']
    for stim in stimuli:
        c0 = data[stim]['control']['summary']['behavior']
        lines += [f"### {stim} (control: turn {c0['turn_mean_abs_deg_per_tic']:.3f}, forward {c0['forward_mean']:.2f}, "
                  f"attack {c0['attack_frac']:.3f})", '',
                  '| Arm | ' + ' | '.join(keys) + ' |', '|---|' + '---|' * len(keys),
                  '| **sham range** | ' + ' | '.join(
                      f"{fmt[k].format(sham_range(stim, k)[0])} … {fmt[k].format(sham_range(stim, k)[1])}" for k in keys) + ' |']
        for arm in TARGETS + VISION:
            m = data[stim][arm]['measures']
            lines.append(f'| {arm} | ' + ' | '.join(
                fmt[k].format(m[k]) + (' ◆' if beyond(stim, arm, k) else '') for k in keys) + ' |')
        lines.append('')
    lines.append('◆ = larger in size than every sham on this stimulus.')

    # 2. Specific effects: every stimulus, same sign.
    lines += ['', '## Specific effects (all stimuli, same direction)', '']
    for arm in TARGETS:
        found = []
        for k in keys:
            sides = [beyond(s, arm, k) for s in stimuli]
            if sides[0] and all(x == sides[0] for x in sides):
                found.append((k, [data[s][arm]['measures'][k] for s in stimuli]))
        sham_td = {s: np.stack([data[s][x]['type_delta'] for x in shams]) for s in stimuli}
        sides = np.stack([np.where(np.abs(data[s][arm]['type_delta']) > np.abs(sham_td[s]).max(0),
                                   np.sign(data[s][arm]['type_delta']), 0) for s in stimuli])
        # Knocked-out cells are already excluded from type_delta, so their own type can't pass trivially.
        specific = np.flatnonzero((sides[0] != 0) & (sides == sides[0]).all(0))
        rows = sorted(specific, key=lambda i: -abs(np.mean([data[s][arm]['type_delta'][i] for s in stimuli])))
        lines += [f'### {arm}', '']
        lines += [f"- **{k}**: " + ', '.join(f'{s} {fmt[k].format(v)}' for s, v in zip(stimuli, vals)) for k, vals in found]
        if not found:
            lines.append('- No behavior or network-size measure is specific.')
        lines += ['', f'{len(rows)} cell types changed rate more than any sham, in every stimulus:', '']
        if rows:
            lines += ['| Cell type | superclass | ' + ' | '.join(f'Δ Hz {s} (sham range)' for s in stimuli) + ' |',
                      '|---|---|' + '---|' * len(stimuli)]
            for i in rows[:25]:
                lines.append(f'| {type_names[i]} | {superclass_of[type_names[i]]} | ' + ' | '.join(
                    f"{data[s][arm]['type_delta'][i]:+.3f} ({sham_td[s][:, i].min():+.3f} … {sham_td[s][:, i].max():+.3f})"
                    for s in stimuli) + ' |')
            if len(rows) > 25:
                lines.append(f'| … {len(rows) - 25} more in comparison.json | | ' + ' | ' * (len(stimuli) - 1) + ' |')
        lines.append('')
        out['arms'][arm] = {
            'specific_measures': {k: v for k, v in found},
            'specific_cell_types': [{'cell_type': str(type_names[i]), 'superclass': str(superclass_of[type_names[i]]),
                                     'delta_hz': {s: float(data[s][arm]['type_delta'][i]) for s in stimuli},
                                     'sham_range_hz': {s: [float(sham_td[s][:, i].min()), float(sham_td[s][:, i].max())]
                                                       for s in stimuli}} for i in rows],
            'per_stimulus': {s: data[s][arm]['measures'] for s in stimuli}}

    # 3. Spike totals of the watched cell types, so the w-cHIN question has its own table.
    lines += ['## Watched cell types: total spikes', '',
              '| Stimulus | Arm | ' + ' | '.join(WATCH) + ' |', '|---|---|' + '---|' * len(WATCH)]
    for stim in stimuli:
        def spikes(arm, t):
            r = load(stim, arm)
            return int(r['counts'][types['cell_type'] == t].sum())
        for arm in ['control'] + TARGETS:
            lines.append(f'| {stim} | {arm} | ' + ' | '.join(str(spikes(arm, t)) for t in WATCH) + ' |')
        sham_vals = {t: [spikes(x, t) for x in shams] for t in WATCH}
        lines.append(f'| {stim} | sham range | ' + ' | '.join(f'{min(v)} … {max(v)}' for v in sham_vals.values()) + ' |')

    (RESULTS / 'comparison.md').write_text('\n'.join(lines) + '\n')
    (RESULTS / 'comparison.json').write_text(json.dumps(out, indent=2) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
