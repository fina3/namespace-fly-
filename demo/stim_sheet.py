"""Pack the first 350 input frames of a stimulus into demo/stim-<s>.jpg (25 x 14 tiles of 128 x 96).

Run on a Devbox after `run_condition.py --dump-frames <dir>`. Every frame is checked against the
experiment's own ticks.csv (frame_sha16 = sha256 of the raw frame) before it goes into the sheet.

  python stim_sheet.py <frames-dir> <ticks.csv> <out.jpg>
"""
import csv, hashlib, sys
from pathlib import Path
import numpy as np
from PIL import Image

TICS, FW, FH, COLS = 350, 128, 96, 25


def main(frames, ticks, out):
    with open(ticks) as f:
        want = [r['frame_sha16'] for r in csv.DictReader(f)][:TICS]
    sheet = Image.new('RGB', (COLS * FW, (TICS + COLS - 1) // COLS * FH))
    for i in range(TICS):
        im = Image.open(Path(frames) / f'{i + 1:04d}.png').convert('RGB')
        got = hashlib.sha256(np.asarray(im).tobytes()).hexdigest()[:16]
        if got != want[i]:
            sys.exit(f'tick {i + 1}: frame hash {got} != ticks.csv {want[i]}')
        sheet.paste(im.resize((FW, FH), Image.LANCZOS), ((i % COLS) * FW, (i // COLS) * FH))
    sheet.save(out, quality=88)
    print(f'{TICS} frames match ticks.csv; wrote {out} {sheet.size}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
