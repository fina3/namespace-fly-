"""Demo loop for a macOS Devbox screen: one process, the picture never goes away.

Cycles intact -> DNp20 off -> DNpe017 off -> MeVP9 off forever. The brain stays loaded between
games; synapse weights are restored from a copy before each knockout, so every game is a clean
intervention. Closed loop: the brain's decoded commands move the player.

The screen is drawn for the dashboard's Live view, which refreshes about once a second:
  --speed    game tics per wall second (35 = real time). 7 is 5x slow motion: one dashboard frame
             then shows 7 tics of motion instead of 35, so the tile reads as a moving game.
  --hud      draw our own full-screen window: the game frame, the condition, a survival timer,
             TURN / MOVE / FIRE lights, ALIVE / DEAD, and survival bars that accumulate over the
             session, so a single still frame tells the whole story. ViZDoom renders at its normal
             640x480 and stays hidden, so these games sample the same raster as the experiment.
  --hold     seconds the death frame stays up before the next game.
Without --hud the real ViZDoom window is shown instead (the old wall).
"""
import argparse, json, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fly_sim

CYCLE = [('INTACT BRAIN', []), ('DNp20 OFF', [10059, 10162]), ('DNpe017 OFF', [10527, 555871]), ('MeVP9 OFF', [12764, 12356])]
TICS = 35   # game tics per second of game time


class Hud:
    """Full-screen pygame window: game frame plus the state the Live view needs to show at 1 fps."""

    BG, TEXT, MUTED, DIM, ON, DEAD, PANEL = (7, 9, 13), (230, 237, 243), (107, 122, 140), (42, 51, 63), (92, 242, 176), (255, 107, 107), (13, 17, 24)

    def __init__(self, font_path, label):
        import os
        os.environ.setdefault('SDL_VIDEO_ALLOW_SCREENSAVER', '0')
        import pygame
        self.pg = pygame
        pygame.init()
        info = pygame.display.Info()
        self.w, self.h = info.current_w, info.current_h
        self.screen = pygame.display.set_mode((self.w, self.h), pygame.FULLSCREEN)   # covers the menu bar and the Dock
        pygame.display.set_caption('DOOMFLY')
        pygame.mouse.set_visible(False)
        u = self.h / 100   # 1 unit = 1% of screen height
        self.u = u
        path = font_path if font_path and Path(font_path).exists() else None
        self.f_title = pygame.font.Font(path, int(5.5 * u)); self.f_title.set_bold(True)
        self.f_big = pygame.font.Font(path, int(7 * u)); self.f_big.set_bold(True)
        self.f_mid = pygame.font.Font(path, int(3 * u))
        self.f_small = pygame.font.Font(path, int(2.3 * u))
        self.label = label
        self.history = {name: [] for name, _ in CYCLE}

    def text(self, font, s, color, x, y, anchor='topleft'):
        surf = font.render(s, True, color)
        rect = surf.get_rect(**{anchor: (x, y)})
        self.screen.blit(surf, rect)
        return rect

    def draw(self, frame, name, ids, seconds, kills, action, dead, game_no):
        pg, u, S = self.pg, self.u, self.screen
        for e in pg.event.get():
            if e.type == pg.QUIT:
                raise SystemExit
        S.fill(self.BG)
        m = 3 * u
        # header: condition and what is silenced
        self.text(self.f_title, name, self.TEXT, m, m)
        ko = 'no neurons silenced' if not ids else 'silenced: ' + ' + '.join(str(i) for i in ids)
        self.text(self.f_mid, ko, self.MUTED, m, m + 7 * u)
        # game frame at its own 4:3 on the left; the panel takes what is left on the right
        top, bottom = m + 11.5 * u, self.h - m - 14 * u
        fh, fw = frame.shape[:2]
        box = pg.Rect(m, top, int((bottom - top) * fw / fh), bottom - top)
        panel_w = self.w - m - box.right - m
        scale = min(box.w / fw, box.h / fh)
        tw, th = int(fw * scale), int(fh * scale)
        surf = pg.image.frombuffer(np.ascontiguousarray(frame).tobytes(), (fw, fh), 'RGB')
        surf = pg.transform.scale(surf, (tw, th))
        if dead:
            arr = pg.surfarray.pixels3d(surf)
            grey = (arr[..., 0] * .3 + arr[..., 1] * .59 + arr[..., 2] * .11) * .55
            arr[..., 0] = arr[..., 1] = arr[..., 2] = grey.astype(np.uint8)
            del arr
        dst = surf.get_rect(center=box.center)
        pg.draw.rect(S, (0, 0, 0), box, border_radius=int(1.5 * u))
        S.blit(surf, dst)
        # right panel: survival bars from the games already played on this box
        px = box.right + m
        self.text(self.f_small, 'SURVIVAL THIS SESSION', self.MUTED, px, top)
        longest = max([60.0] + [s for v in self.history.values() for s in v])
        y = top + 4 * u
        for cname, _ in CYCLE:
            runs = self.history[cname]
            self.text(self.f_small, cname, self.TEXT if cname == name else self.MUTED, px, y)
            bar = pg.Rect(px, y + 3 * u, panel_w, 1.6 * u)
            pg.draw.rect(S, self.DIM, bar, border_radius=int(.8 * u))
            if runs:
                mean = sum(runs) / len(runs)
                fill = pg.Rect(px, y + 3 * u, max(1, int(panel_w * mean / longest)), 1.6 * u)
                pg.draw.rect(S, self.ON if cname == 'INTACT BRAIN' else self.TEXT, fill, border_radius=int(.8 * u))
                self.text(self.f_small, f'{mean:.0f} s  ·  {len(runs)} game{"s" if len(runs) != 1 else ""}', self.MUTED, px + panel_w, y, 'topright')
            elif cname == name:
                self.text(self.f_small, 'playing', self.MUTED, px + panel_w, y, 'topright')
            y += 7 * u
        # footer: timer, lights, status
        fy = self.h - m - 11 * u
        self.text(self.f_small, 'SURVIVAL', self.MUTED, m, fy)
        self.text(self.f_big, f'{int(seconds // 60):02d}:{seconds % 60:04.1f}', self.TEXT, m, fy + 2.4 * u)
        self.text(self.f_small, 'KILLS', self.MUTED, m + 42 * u, fy)
        self.text(self.f_big, str(kills), self.TEXT, m + 42 * u, fy + 2.4 * u)
        x = m + 56 * u
        for key, word in (('turn', 'TURN'), ('forward', 'MOVE'), ('attack', 'FIRE')):
            on = (not dead) and action is not None and abs(float(action.get(key, 0))) > 1e-6
            pg.draw.circle(S, self.ON if on else self.DIM, (int(x + 1.2 * u), int(fy + 6.2 * u)), int(1.2 * u))
            r = self.text(self.f_mid, word, self.TEXT if on else self.MUTED, x + 3.2 * u, fy + 6.2 * u, 'midleft')
            x = r.right + 3 * u
        status = 'DEAD' if dead else 'ALIVE'
        self.text(self.f_big, status, self.DEAD if dead else self.ON, self.w - m, fy + 2.4 * u, 'topright')
        self.text(self.f_small, f'{self.label}  ·  game {game_no}', self.MUTED, self.w - m, bottom - 2.3 * u, 'topright')
        pg.display.flip()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--doomfly', required=True)
    p.add_argument('--seed', type=int, default=41027)
    p.add_argument('--speed', type=float, default=7, help='game tics per wall second; 35 = real time')
    p.add_argument('--max-seconds', type=float, default=60, help='game-time limit per game')
    p.add_argument('--hold', type=float, default=8, help='seconds the final frame stays up after a death')
    p.add_argument('--hud', action='store_true', help='draw our own full-screen HUD instead of the ViZDoom window')
    p.add_argument('--font', default='', help='TTF for the HUD (Inter)')
    p.add_argument('--label', default='', help='shown in the HUD corner, e.g. the box name')
    p.add_argument('--resolution', help='ViZDoom window resolution when not using --hud')
    args = p.parse_args()

    brain, manifest, _ = fly_sim.load(args.doomfly)
    from doom.engine import NeuralControls
    from doom.game import Game, retinal_samples
    import vizdoom as vzd
    if not args.hud:
        vzd.DoomGame.set_window_visible = lambda self, visible: None          # DOOMFLY hides it; leave it visible
        if args.resolution:
            res = getattr(vzd.ScreenResolution, 'RES_' + args.resolution.upper())
            set_res = vzd.DoomGame.set_screen_resolution
            vzd.DoomGame.set_screen_resolution = lambda self, r: set_res(self, res)
    hud = Hud(args.font, args.label) if args.hud else None
    tick_s = 1 / args.speed
    draw_every = max(1, int(round(args.speed / 10)))   # at most ~10 redraws per wall second

    weights0 = brain.weight.copy()
    game = Game(seed=args.seed, scenario='combat_survival', spectator=False)
    tick, game_no = 0, 0
    while True:
        for name, ids in CYCLE:
            game_no += 1
            brain.weight[:] = weights0
            targets, _, _ = fly_sim.silence(brain, fly_sim.indices_of(brain, ids)) if ids else (np.zeros(0, dtype=np.int32), 0, 0)
            if len(targets):   # a cell switched off mid-run may still hold charge from the last game; put it at rest
                brain.v[targets] = -52.0
                brain.g[targets] = 0.0
                brain.refractory[targets] = 0
            controls = NeuralControls(manifest['readouts'], mode='bci')
            game.new_episode()
            start, t0 = tick, time.perf_counter()
            silenced_spikes, action, obs = 0, None, {'finished': False, 'kills': 0}
            frame = game.pixels()
            while tick - start < args.max_seconds * TICS:
                tick += 1
                frame = game.pixels()
                light = retinal_samples(frame, brain.uv)
                steps = int(round(tick * 10000 / 35)) - brain.cursor
                counts, _ = brain.step(light, steps * .1)
                action = controls.decode(counts, steps * .1 / 1000)
                silenced_spikes += int(counts[targets].sum()) if len(targets) else 0
                game.act(action)
                obs = game.observation()
                if hud and (tick - start) % draw_every == 0:
                    hud.draw(frame, name, ids, (tick - start) / TICS, obs['kills'], action, False, game_no)
                if obs['finished']:
                    break
                ahead = (tick - start) * tick_s - (time.perf_counter() - t0)
                if ahead > 0:
                    time.sleep(ahead)
            survived = (tick - start) / TICS
            if hud:
                hud.history[name].append(survived)
                hud.draw(frame, name, ids, survived, obs['kills'], action, obs['finished'], game_no)
            print(json.dumps({'condition': name, 'seed': args.seed, 'survived_s': round(survived, 1),
                              'wall_s': round(time.perf_counter() - t0, 1), 'died': obs['finished'], 'kills': obs['kills'],
                              'silenced_spikes': silenced_spikes}), flush=True)
            if silenced_spikes:   # should not happen after the reset above; report, but keep the wall running
                print(json.dumps({'warning': 'silenced neurons spiked', 'condition': name, 'spikes': silenced_spikes}), flush=True)
            end = time.perf_counter() + args.hold
            while time.perf_counter() < end:
                if hud:
                    hud.draw(frame, name, ids, survived, obs['kills'], action, obs['finished'], game_no)
                time.sleep(0.25)


if __name__ == '__main__':
    main()
