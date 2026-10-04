"""Search for small neuron knockouts that survive longer in Doom than the intact brain.

  python run_survival_search.py --num-candidates 100 --knockout-size 2 \\
      --candidate-seed 42 --game-seeds 1,2,3 --max-tics 4200 --devboxes fly-control

Steps (all by default, or pick with --steps):
  generate  draw the candidates with a fixed seed and save manifest.json
  assign    split (candidate, game seed) jobs across the machines
  run       ship the jobs to the Devboxes, run them, pull the result files back
  collect   merge the per-run results, compare with the intact brain, rank

Candidate 0 is always the intact brain, run on exactly the same game seeds.
Every job is one independent `run_candidate.py` call, so `run` can be replaced by
any other way of executing the commands in jobs-*.json.

This ranks behavior of the DOOMFLY simulation. It is not evidence about real flies.
"""
import argparse, csv, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIRECT_INPUT_TYPES = ['R1-R6', 'L1', 'L2', 'L3', 'L5']   # receive external current in DOOMFLY; cannot be fully silenced
SHIP = ['fly_sim.py', 'run_candidate.py', 'live.html', 'run_survival_search.py']
REMOTE = '/workspaces/namespace-fly'


# ---------------------------------------------------------------- generate
def candidate_pool():
    """Neurons that fire in the intact control run and can be fully silenced, sorted by ID."""
    import numpy as np
    types = np.load(HERE / 'neuron_types.npz')
    counts = np.load(HERE / 'results/s1/control/neuron_counts.npz')
    assert (types['ids'] == counts['ids']).all()
    ok = (counts['counts'] > 0) & ~np.isin(types['cell_type'], DIRECT_INPUT_TYPES)
    return np.sort(types['ids'][ok])


def generate(args, out):
    import numpy as np
    pool = candidate_pool()
    rng = np.random.default_rng(args.candidate_seed)
    seen, candidates = set(), []
    while len(candidates) < args.num_candidates:
        combo = tuple(sorted(int(x) for x in rng.choice(pool, size=args.knockout_size, replace=False)))
        if combo not in seen:
            seen.add(combo)
            candidates.append({'candidate_id': len(candidates) + 1, 'neurons': list(combo)})
    manifest = {
        'candidate_seed': args.candidate_seed, 'knockout_size': args.knockout_size,
        'num_candidates': args.num_candidates, 'game_seeds': args.game_seeds, 'max_tics': args.max_tics,
        'pool': {'size': int(len(pool)),
                 'rule': 'fires in results/s1/control and is not a directly driven input cell '
                         f'({", ".join(DIRECT_INPUT_TYPES)})'},
        'code_commit': git_commit(),
        'candidates': [{'candidate_id': 0, 'neurons': []}] + candidates,
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(f'generated {len(candidates)} candidates of size {args.knockout_size} from a pool of {len(pool)} '
          f'(seed {args.candidate_seed}) + intact baseline')
    return manifest


def retest(args, out):
    """Manifest for re-running the best candidates of an earlier search on new game seeds."""
    prev = json.loads(Path(args.retest).read_text())
    ranked = [c for c in prev['ranking'] if c['candidate_id']][:args.top]
    overlap = set(args.game_seeds) & set(prev['manifest']['game_seeds'])
    if overlap:
        sys.exit(f'retest seeds must be fresh; {sorted(overlap)} were used in the screen')
    manifest = {
        'candidate_seed': prev['manifest']['candidate_seed'], 'knockout_size': prev['manifest']['knockout_size'],
        'num_candidates': len(ranked), 'game_seeds': args.game_seeds, 'max_tics': args.max_tics,
        'retest_of': {'results': args.retest, 'screen_seeds': prev['manifest']['game_seeds'], 'top': args.top},
        'pool': prev['manifest']['pool'], 'code_commit': git_commit(),
        'candidates': [{'candidate_id': 0, 'neurons': []}] + [{'candidate_id': c['candidate_id'], 'neurons': c['knockout_neurons'],
                                                              'screen_survival_ratio': c['survival_ratio']} for c in ranked],
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(f're-testing the top {len(ranked)} candidates of {args.retest} on fresh seeds {args.game_seeds}')
    return manifest


def git_commit():
    r = subprocess.run(['git', '-C', str(HERE), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    dirty = subprocess.run(['git', '-C', str(HERE), 'status', '--porcelain', '--untracked-files=no'],
                           capture_output=True, text=True).stdout.strip()
    return r.stdout.strip() + ('-dirty' if dirty else '')


# ---------------------------------------------------------------- assign
def assign(manifest, machines, out):
    jobs = [{'candidate_id': c['candidate_id'], 'neurons': c['neurons'], 'game_seed': s,
             'max_tics': manifest['max_tics'], 'candidate_seed': manifest['candidate_seed'],
             'code_commit': manifest['code_commit']}
            for c in manifest['candidates'] for s in manifest['game_seeds']]
    split = {m: jobs[i::len(machines)] for i, m in enumerate(machines)}
    for m, js in split.items():
        (out / f'jobs-{m}.json').write_text(json.dumps(js, indent=1) + '\n')
    print(f'assigned {len(jobs)} runs: ' + ', '.join(f'{m} {len(js)}' for m, js in split.items()))
    return split


def command(job, runs_dir, extra=()):
    return ['run_candidate.py', '--candidate-id', str(job['candidate_id']),
            '--neurons', ','.join(map(str, job['neurons'])), '--game-seed', str(job['game_seed']),
            '--max-tics', str(job['max_tics']), '--candidate-seed', str(job['candidate_seed']),
            '--code-commit', job['code_commit'], '--out', str(runs_dir), *extra]


# ---------------------------------------------------------------- worker (runs on the machine doing the simulations)
def worker(argv):
    p = argparse.ArgumentParser(prog='run_survival_search.py worker')
    p.add_argument('--jobs', required=True)
    p.add_argument('--runs', required=True)
    p.add_argument('--par', type=int, default=12, help='simulations at once (each uses one core and ~0.5 GB)')
    p.add_argument('--python', default=os.environ.get('FLY_VENV', '/workspaces/venv') + '/bin/python')
    p.add_argument('--doomfly', default=os.environ.get('FLY_DOOMFLY', '/workspaces/doomfly'))
    p.add_argument('--trace', action='store_true')
    a = p.parse_args(argv)
    jobs = json.loads(Path(a.jobs).read_text())
    runs = Path(a.runs); runs.mkdir(parents=True, exist_ok=True)
    logs = runs.parent / 'logs'; logs.mkdir(exist_ok=True)

    def one(job):
        name = f"c{job['candidate_id']:04d}-s{job['game_seed']}"
        if (runs / f'{name}.json').exists():
            return name, 'skip'
        work = runs.parent / 'work' / name   # ViZDoom writes ./_vizdoom in its cwd; parallel runs must not share one
        work.mkdir(parents=True, exist_ok=True)
        cmd = [a.python, str(HERE / 'run_candidate.py')] + command(job, runs, (['--trace'] if a.trace else []) + ['--doomfly', a.doomfly])[1:]
        with open(logs / f'{name}.log', 'w') as log:
            code = subprocess.run(cmd, cwd=work, stdout=log, stderr=subprocess.STDOUT).returncode
        return name, 'ok' if code == 0 and (runs / f'{name}.json').exists() else 'FAIL'

    with ThreadPoolExecutor(a.par) as pool:
        done = list(pool.map(one, jobs))
    failed = [n for n, s in done if s == 'FAIL']
    print(f"{sum(s == 'ok' for _, s in done)} ok, {sum(s == 'skip' for _, s in done)} already done, {len(failed)} failed"
          + (f': {failed}' if failed else ''))
    sys.exit(1 if failed else 0)


# ---------------------------------------------------------------- run on Namespace Devboxes
def devbox(*a, check=True):
    r = subprocess.run(['devbox', *a], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"devbox {' '.join(a[:3])} failed: {(r.stderr or r.stdout).strip()[-300:]}")
    return r.stdout


def run_on_devbox(box, out, par, trace):
    remote_out = f'{REMOTE}/survival/{out.name}'
    for f in SHIP:
        devbox('upload', box, str(HERE / f), f'{REMOTE}/{f}', '--mkdir')
    devbox('upload', box, str(out / f'jobs-{box}.json'), f'{remote_out}/jobs.json', '--mkdir')
    r = subprocess.run(['devbox', 'exec', box, '--', 'bash', '-lc',
                        'P=$([ -n "$FLY_VENV" ] && echo "$FLY_VENV/bin/python" || echo python3); '
                        f'$P {REMOTE}/run_survival_search.py worker --jobs {remote_out}/jobs.json '
                        f'--runs {remote_out}/runs --par {par}' + (' --trace' if trace else '')],
                       capture_output=True, text=True)
    summary = [l for l in r.stdout.splitlines() if ' ok, ' in l]
    devbox('exec', box, '--', 'bash', '-lc', f'cd {remote_out} && tar -czf runs.tgz runs')
    devbox('download', box, f'{remote_out}/runs.tgz', str(out / f'runs-{box}.tgz'))
    subprocess.run(['tar', '-xzf', str(out / f'runs-{box}.tgz'), '-C', str(out)], check=True)
    os.remove(out / f'runs-{box}.tgz')
    return f"{box}: {summary[-1] if summary else 'no summary; exit ' + str(r.returncode)}", r.returncode


# ---------------------------------------------------------------- collect + rank
def collect(manifest, out):
    runs = {}
    for f in sorted((out / 'runs').glob('c*-s*.json')):
        r = json.loads(f.read_text())
        runs[(r['candidate_id'], r['game_seed'])] = r
    seeds = manifest['game_seeds']
    missing = [(c['candidate_id'], s) for c in manifest['candidates'] for s in seeds if (c['candidate_id'], s) not in runs]
    intact = {s: runs[(0, s)] for s in seeds if (0, s) in runs}
    if len(intact) != len(seeds):
        sys.exit(f'intact baseline missing for seeds {[s for s in seeds if s not in intact]}')

    rows = []
    for c in manifest['candidates']:
        for s in seeds:
            r = runs.get((c['candidate_id'], s))
            if r is None:
                continue
            if r['knockout_neurons'] != c['neurons'] or r['silenced_spikes'] != 0 or r['max_tics'] != manifest['max_tics']:
                sys.exit(f"result c{c['candidate_id']} seed {s} does not match the manifest")
            if r['provenance']['first_frame_sha256'] != intact[s]['provenance']['first_frame_sha256']:
                sys.exit(f"candidate {c['candidate_id']} seed {s} did not start from the intact run's first frame")
            row = {k: r[k] for k in ['candidate_id', 'knockout_neurons', 'game_seed', 'survival_tics', 'survival_seconds',
                                     'died', 'turn_output', 'move_output', 'fire_output', 'turning_fraction',
                                     'movement_fraction', 'firing_fraction', 'distance_moved', 'kills', 'min_health']}
            row['intact_survival_tics'] = intact[s]['survival_tics']
            row['survival_ratio'] = round(r['survival_tics'] / intact[s]['survival_tics'], 3)
            rows.append(row)

    summary = []
    for c in manifest['candidates']:
        mine = [r for r in rows if r['candidate_id'] == c['candidate_id']]
        if not mine:
            continue
        n = len(mine)
        summary.append({
            'candidate_id': c['candidate_id'], 'knockout_neurons': c['neurons'], 'seeds_run': n,
            'mean_survival_seconds': round(sum(r['survival_seconds'] for r in mine) / n, 2),
            # Total time alive over total intact time alive on the same seeds. Averaging per-seed
            # ratios instead would be inflated by any seed where intact happens to die early.
            'survival_ratio': round(sum(r['survival_tics'] for r in mine) / sum(r['intact_survival_tics'] for r in mine), 3),
            'min_survival_ratio': min(r['survival_ratio'] for r in mine),
            'seeds_beating_intact': sum(r['survival_tics'] > r['intact_survival_tics'] for r in mine),
            'seeds_hit_time_limit': sum(not r['died'] for r in mine),
            'mean_movement_fraction': round(sum(r['movement_fraction'] for r in mine) / n, 3),
            'mean_firing_fraction': round(sum(r['firing_fraction'] for r in mine) / n, 3),
            'mean_turning_fraction': round(sum(r['turning_fraction'] for r in mine) / n, 3),
            'total_kills': sum(r['kills'] for r in mine),
        })
    ranked = sorted(summary, key=lambda x: (-x['survival_ratio'], x['candidate_id']))

    with open(out / 'results.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({**r, 'knockout_neurons': '+'.join(map(str, r['knockout_neurons']))})
    (out / 'results.json').write_text(json.dumps(
        {'manifest': {k: v for k, v in manifest.items() if k != 'candidates'}, 'intact': {str(s): intact[s]['survival_tics'] for s in seeds},
         'missing_runs': missing, 'ranking': ranked, 'runs': rows}, indent=1) + '\n')

    capped = [s for s in seeds if not intact[s]['died']]
    print(f"\nINTACT BASELINE  " + '  '.join(
        f"seed {s}: {intact[s]['survival_seconds']:.1f} s{'' if intact[s]['died'] else ' (time limit)'}" for s in seeds))
    if capped:
        print(f'  note: intact reached the time limit on seeds {capped}; no candidate can beat it there (ratio capped at 1.0)')
    print(f"\n{'RANK':<5} {'KNOCKOUT':<26} {'SURVIVAL':>9} {'VS INTACT':>10} {'BEAT':>6} {'MOVE':>6} {'FIRE':>6} {'KILLS':>6}")
    shown = 0
    for i, r in enumerate(ranked, 1):
        if shown >= 15 and r['candidate_id'] != 0:
            continue
        label = 'INTACT (baseline)' if r['candidate_id'] == 0 else ' + '.join(map(str, r['knockout_neurons']))
        print(f"{i:<5} {label:<26} {r['mean_survival_seconds']:>7.1f} s {r['survival_ratio']:>9.2f}x "
              f"{r['seeds_beating_intact']:>3}/{r['seeds_run']:<2} {100*r['mean_movement_fraction']:>5.0f}% "
              f"{100*r['mean_firing_fraction']:>5.0f}% {r['total_kills']:>6}")
        shown += 1
    better = [r for r in ranked if r['candidate_id'] and r['seeds_beating_intact'] == r['seeds_run']]
    print(f"\n{len(better)} of {len(ranked) - 1} candidates outlived intact on every seed"
          + (f'; {len(missing)} runs missing' if missing else ''))
    print('SURVIVAL = mean over seeds. VS INTACT = total time alive / intact total on the same seeds. '
          'BEAT = seeds where it outlived intact. MOVE/FIRE = share of tics with that command.')
    if len(seeds) < 5:
        print('WARNING: fewer than 5 game seeds. Intact survival varies widely between seeds, so this ranking is mostly luck.')
    print(f'wrote {out}/results.csv and results.json')


# ---------------------------------------------------------------- main
def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'worker':
        return worker(sys.argv[2:])
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--num-candidates', type=int, default=100)
    p.add_argument('--knockout-size', type=int, default=2)
    p.add_argument('--candidate-seed', type=int, default=42)
    p.add_argument('--game-seeds', default='1', type=lambda s: [int(x) for x in s.split(',')])
    p.add_argument('--max-tics', type=int, default=4200)
    p.add_argument('--name', help='results folder under results/survival/ (default: built from the settings)')
    p.add_argument('--devboxes', default='', type=lambda s: [x for x in s.split(',') if x],
                   help='Devbox names to run on; they must already be set up with setup.sh')
    p.add_argument('--par', type=int, default=12)
    p.add_argument('--trace', action='store_true')
    p.add_argument('--steps', default='generate,assign,run,collect', type=lambda s: s.split(','))
    p.add_argument('--retest', help='results.json of an earlier search: re-run its top candidates instead of drawing new ones')
    p.add_argument('--top', type=int, default=10, help='with --retest: how many of the best candidates to re-run')
    args = p.parse_args()

    name = args.name or f'k{args.knockout_size}-n{args.num_candidates}-c{args.candidate_seed}'
    out = HERE / 'results/survival' / name
    out.mkdir(parents=True, exist_ok=True)

    if 'generate' in args.steps and args.retest:
        manifest = retest(args, out)
    elif 'generate' in args.steps:
        manifest = generate(args, out)
    else:
        manifest = json.loads((out / 'manifest.json').read_text())
    machines = args.devboxes or ['local']
    if 'assign' in args.steps:
        assign(manifest, machines, out)
    if 'run' in args.steps:
        if not args.devboxes:
            sys.exit('--devboxes is required for the run step (or run the commands in jobs-local.json yourself)')
        with ThreadPoolExecutor(len(machines)) as pool:
            results = list(pool.map(lambda b: run_on_devbox(b, out, args.par, args.trace), machines))
        for line, _ in results:
            print(line)
        if any(code for _, code in results):
            sys.exit('some runs failed; fix and rerun (finished runs are skipped)')
    if 'collect' in args.steps:
        collect(manifest, out)


if __name__ == '__main__':
    main()
