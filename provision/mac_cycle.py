"""Demo loop for a macOS Devbox screen: one process, the game window never closes.

Cycles intact -> DNp20 off -> DNpe017 off -> MeVP9 off forever. The brain stays loaded between
games; synapse weights are restored from a copy before each knockout, so every game is a clean
intervention. Closed loop, real-time pace, visible ViZDoom window. Demo only: the window is
rendered large, so the retina samples a different raster than in the experiment.
"""
import argparse, json, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fly_sim

CYCLE = [('intact', []), ('DNp20 off', [10059, 10162]), ('DNpe017 off', [10527, 555871]), ('MeVP9 off', [12764, 12356])]
TICK_S = 1 / 35


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--doomfly', required=True)
    p.add_argument('--seed', type=int, default=41027)
    p.add_argument('--resolution', default='1600x1200')
    p.add_argument('--max-seconds', type=float, default=60)
    p.add_argument('--hold', type=float, default=3, help='seconds the final frame stays up after a death')
    args = p.parse_args()

    brain, manifest, _ = fly_sim.load(args.doomfly)
    from doom.engine import NeuralControls
    from doom.game import Game, retinal_samples
    import vizdoom as vzd
    vzd.DoomGame.set_window_visible = lambda self, visible: None          # DOOMFLY hides it; leave it visible
    res = getattr(vzd.ScreenResolution, 'RES_' + args.resolution.upper())
    set_res = vzd.DoomGame.set_screen_resolution
    vzd.DoomGame.set_screen_resolution = lambda self, r: set_res(self, res)

    weights0 = brain.weight.copy()
    game = Game(seed=args.seed, scenario='combat_survival', spectator=False)
    tick = 0
    while True:
        for name, ids in CYCLE:
            brain.weight[:] = weights0
            targets, _, _ = fly_sim.silence(brain, fly_sim.indices_of(brain, ids)) if ids else (np.zeros(0, dtype=np.int32), 0, 0)
            controls = NeuralControls(manifest['readouts'], mode='bci')
            game.new_episode()
            start, t0 = tick, time.perf_counter()
            silenced_spikes = 0
            while tick - start < args.max_seconds * 35:
                tick += 1
                frame = game.pixels()
                light = retinal_samples(frame, brain.uv)
                steps = int(round(tick * 10000 / 35)) - brain.cursor
                counts, _ = brain.step(light, steps * .1)
                action = controls.decode(counts, steps * .1 / 1000)
                silenced_spikes += int(counts[targets].sum()) if len(targets) else 0
                game.act(action)
                obs = game.observation()
                if obs['finished']:
                    break
                ahead = (tick - start) * TICK_S - (time.perf_counter() - t0)
                if ahead > 0:
                    time.sleep(ahead)
            print(json.dumps({'condition': name, 'seed': args.seed, 'survived_s': round((tick - start) / 35, 1),
                              'died': obs['finished'], 'kills': obs['kills'], 'silenced_spikes': silenced_spikes}), flush=True)
            if silenced_spikes:
                raise RuntimeError('silenced neurons spiked')
            time.sleep(args.hold)


if __name__ == '__main__':
    main()
