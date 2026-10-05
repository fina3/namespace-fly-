"""One knockout candidate playing Doom in closed loop until it dies or time runs out.

Every tic: the game frame drives the simulated fly brain, the decoded TURN / MOVE /
FIRE commands are applied to the game, and the next frame reflects them.
Runs completely on its own, so a coordinator can spread candidates over machines.

  python run_candidate.py --candidate-id 37 --neurons 48122,99102 --game-seed 1

This measures the DOOMFLY simulation. It says nothing about real flies.
"""
import argparse, hashlib, io, json, os, subprocess, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

import fly_sim

HERE = Path(__file__).resolve().parent
TICS_PER_SECOND = 35


class Live:
    """Tiny read-only web view: /  (page), /state (JSON), /frame.jpg (latest frame)."""

    def __init__(self, port):
        self.lock = threading.Lock()
        self.state, self.jpeg = {'status': 'STARTING'}, b''
        live = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = self.path.split('?')[0]
                with live.lock:
                    if path == '/state':
                        body, kind = json.dumps(live.state).encode(), 'application/json'
                    elif path == '/frame.jpg':
                        body, kind = live.jpeg, 'image/jpeg'
                    elif path == '/':
                        body, kind = (HERE / 'live.html').read_bytes(), 'text/html; charset=utf-8'
                    else:
                        self.send_error(404); return
                self.send_response(200)
                self.send_header('Content-Type', kind)
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *a):
                pass

        self.server = ThreadingHTTPServer(('0.0.0.0', port), Handler)  # 0.0.0.0 so a devbox URL can reach it
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def update(self, state, frame=None):
        jpeg = None
        if frame is not None:
            from PIL import Image
            buf = io.BytesIO()
            Image.fromarray(frame).save(buf, format='JPEG', quality=70)
            jpeg = buf.getvalue()
        with self.lock:
            self.state = state
            if jpeg is not None:
                self.jpeg = jpeg


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--candidate-id', type=int, required=True, help='0 is reserved for the intact brain')
    p.add_argument('--neurons', default='', help='comma-separated connectome IDs to silence; empty = intact brain')
    p.add_argument('--game-seed', type=int, required=True)
    p.add_argument('--max-tics', type=int, default=4200, help='time limit in game tics (35 per second)')
    p.add_argument('--candidate-seed', type=int, help='seed that generated this candidate (recorded only)')
    p.add_argument('--code-commit', default='', help='git commit of this repo (recorded only)')
    p.add_argument('--doomfly', default='/workspaces/doomfly')
    p.add_argument('--out', default=str(HERE / 'results/survival/runs'))
    p.add_argument('--trace', action='store_true', help='also save per-tic commands and health as CSV')
    p.add_argument('--live-port', type=int, help='serve the live view on this port')
    p.add_argument('--realtime', action='store_true', help='never run faster than the game clock (for watching live)')
    p.add_argument('--linger', type=float, default=0, help='keep the live view up this many seconds after the run ends')
    p.add_argument('--show-window', action='store_true', help='show the real ViZDoom game window (needs a display; for Live view)')
    p.add_argument('--hold', type=float, default=0, help='keep the game window up this many seconds after the run ends (for Live view)')
    p.add_argument('--resolution', help='render at this ViZDoom resolution instead of 640x480, e.g. 1600x1200 (demo only: '
                   'the retina samples a different raster, so results differ from the experiment)')
    args = p.parse_args()

    ids = [int(x) for x in args.neurons.split(',') if x.strip()]
    if len(set(ids)) != len(ids):
        p.error('duplicate neuron id')
    if (args.candidate_id == 0) != (not ids):
        p.error('candidate 0 is the intact brain and must have no neurons; every other candidate needs some')

    brain, manifest, build = fly_sim.load(args.doomfly)
    from doom.engine import NeuralControls
    from doom.game import Game, retinal_samples
    import vizdoom as vzd

    if args.show_window:   # DOOMFLY hides the window; undo that so the game renders on the box's screen
        hide = vzd.DoomGame.set_window_visible
        vzd.DoomGame.set_window_visible = lambda self, visible: hide(self, True)
    if args.resolution:
        res = getattr(vzd.ScreenResolution, 'RES_' + args.resolution.upper())
        set_res = vzd.DoomGame.set_screen_resolution
        vzd.DoomGame.set_screen_resolution = lambda self, r: set_res(self, res)
    targets, rows_in, rows_out = fly_sim.silence(brain, fly_sim.indices_of(brain, ids))
    controls = NeuralControls(manifest['readouts'], mode='bci')
    game = Game(seed=args.game_seed, scenario='combat_survival', spectator=False)
    live = Live(args.live_port) if args.live_port else None

    def position():
        try:
            return (float(game.game.get_game_variable(vzd.GameVariable.POSITION_X)),
                    float(game.game.get_game_variable(vzd.GameVariable.POSITION_Y)))
        except Exception:
            return None

    def live_state(status, tick, action=None, obs=None):
        return {'candidate_id': args.candidate_id, 'neurons': ids, 'game_seed': args.game_seed, 'status': status,
                'tick': tick, 'seconds': round(tick / TICS_PER_SECOND, 1), 'max_tics': args.max_tics,
                'turn': bool(action and abs(action['turn']) > 1e-6), 'move': bool(action and action['forward'] > 1e-6),
                'fire': bool(action and action['attack']), 'health': obs['health'] if obs else None,
                'kills': obs['kills'] if obs else 0}

    stim_hash = hashlib.sha256()
    first_frame_sha = None
    turn_abs = turn_signed = move_total = 0.0
    turn_tics = move_tics = fire_tics = silenced_spikes = 0
    distance, last_pos = 0.0, position()
    min_health, kills, died, tick = None, 0, False, 0
    trace = []
    wall_start = time.perf_counter()
    for tick in range(1, args.max_tics + 1):
        frame = game.pixels()
        stim_hash.update(frame.tobytes())
        if first_frame_sha is None:
            first_frame_sha = hashlib.sha256(frame.tobytes()).hexdigest()
        light = retinal_samples(frame, brain.uv)
        steps = int(round(tick * 10000 / 35)) - brain.cursor  # 285/286 substeps keep brain and game clocks aligned
        counts, _ = brain.step(light, steps * .1)
        action = controls.decode(counts, steps * .1 / 1000)
        silenced_spikes += int(counts[targets].sum())
        game.act(action)  # closed loop: the brain's commands move the player
        obs = game.observation()

        turn_abs += abs(action['turn']); turn_signed += action['turn']; move_total += action['forward']
        turn_tics += abs(action['turn']) > 1e-6; move_tics += action['forward'] > 1e-6; fire_tics += bool(action['attack'])
        pos = position()
        if pos and last_pos and not obs['finished']:
            distance += float(np.hypot(pos[0] - last_pos[0], pos[1] - last_pos[1]))
        last_pos = pos
        min_health = obs['health'] if min_health is None else min(min_health, obs['health'])
        kills = obs['kills']
        if args.trace:
            trace.append((tick, round(action['turn'], 4), round(action['forward'], 3), int(action['attack']),
                          obs['health'], obs['kills']))
        if obs['finished']:
            died = True
        if live:
            live.update(live_state('DEAD' if died else 'ALIVE', tick, action, obs), None if died else frame)
        if died:
            break
        if args.realtime:
            ahead = tick / TICS_PER_SECOND - (time.perf_counter() - wall_start)
            if ahead > 0:
                time.sleep(ahead)
    wall = time.perf_counter() - wall_start
    if args.hold:
        time.sleep(args.hold)   # the last frame stays on screen
    game.close()

    if silenced_spikes:
        raise RuntimeError('Silenced neurons spiked; knockout failed')

    doomfly_commit = subprocess.run(['git', '-C', args.doomfly, 'rev-parse', 'HEAD'],
                                    capture_output=True, text=True).stdout.strip()
    result = {
        'candidate_id': args.candidate_id,
        'knockout_neurons': ids,
        'game_seed': args.game_seed,
        'survival_tics': tick,
        'survival_seconds': round(tick / TICS_PER_SECOND, 3),
        'died': died,
        'hit_time_limit': not died,
        'max_tics': args.max_tics,
        'turn_output': round(turn_abs, 3),            # total degrees turned (absolute)
        'turn_output_signed': round(turn_signed, 3),
        'move_output': round(move_total, 3),          # sum of forward command over tics
        'fire_output': int(fire_tics),                # tics with the attack button pressed
        'turning_fraction': round(turn_tics / tick, 4),
        'movement_fraction': round(move_tics / tick, 4),
        'firing_fraction': round(fire_tics / tick, 4),
        'distance_moved': round(distance, 1) if last_pos is not None else None,   # map units actually travelled
        'kills': kills,
        'min_health': min_health,
        'silenced_spikes': silenced_spikes,
        'synapse_rows_zeroed': {'incoming': rows_in, 'outgoing': rows_out},
        'provenance': {
            'candidate_seed': args.candidate_seed,
            'code_commit': args.code_commit,
            'doomfly_commit': doomfly_commit,
            'kernel': build,
            'source_hashes': manifest['source_hashes'],
            'first_frame_sha256': first_frame_sha,
            'frames_sha256': stim_hash.hexdigest(),
            'scenario': 'combat_survival', 'decoder': 'bci', 'loop': 'closed',
            'host': os.uname().nodename, 'wall_seconds': round(wall, 1),
        },
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    name = f'c{args.candidate_id:04d}-s{args.game_seed}'
    if args.trace:
        with open(out / f'{name}.trace.csv', 'w') as f:
            f.write('tick,turn,forward,attack,health,kills\n')
            f.writelines(','.join(map(str, row)) + '\n' for row in trace)
    tmp = out / f'{name}.json.partial'
    tmp.write_text(json.dumps(result, indent=1) + '\n')
    tmp.replace(out / f'{name}.json')   # a result file only ever appears complete
    print(json.dumps({k: result[k] for k in ['candidate_id', 'knockout_neurons', 'game_seed', 'survival_tics',
                                             'died', 'movement_fraction', 'firing_fraction', 'kills']}), flush=True)
    if live and args.linger:
        time.sleep(args.linger)


if __name__ == '__main__':
    main()
