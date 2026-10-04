# namespace-fly: a Devbox swarm for fly-brain knockout experiments

A simulated fly-brain intervention experiment on [DOOMFLY](https://github.com/nftechie/doomfly),
which runs the MaleCNS v1.0 fruit-fly connectome (166,700 neurons, 25,582,938 connections) on Doom
frames. A head agent creates **four Namespace Devboxes**. Each runs the same brain on the same
frames, with a different set of neurons silenced. The agent then compares every knockout against
24 sham knockouts.

```text
                              one question
                                   |
                         HEAD AGENT (launch.sh)
                                   |
        +-------------+------------+-------------+--------------+
        v             v                          v              v
   fly-control   fly-dnp20-off           fly-dnpe017-off   fly-both-off
   + MeVP9-off follow-up                                              
   + blank/frozen vision         each box: 3 stimuli (s1, s2, s3)
        |             |                          |              |
        +------ 24 sham knockouts × 3 stimuli, spread over all 4 ------+
                                   |
            identical Doom frames in every run (hash-verified)
                                   |
                    compare.py → one combined result
```

**93 runs × 120 s of simulated time, about 13 minutes of wall time on 4 Devboxes.** A full rerun
reproduced all 79 overlapping runs from an earlier launch byte for byte, including all 166,700
neuron counts, even though many ran on a different Devbox the second time.

## The arms

| Arm | Silenced | Role |
|---|---|---|
| control | nothing | baseline |
| dnp20-off | DNp20 L+R (10162, 10059) | sanity check: the decoder reads turning from DNp20 |
| dnpe017-off | DNpe017 L+R (10527, 555871) | sanity check: the decoder reads movement and firing from DNpe017 |
| both-off | DNp20 + DNpe017 together | both decoder pathways at once |
| mevp9-off | MeVP9 12764 + 12356 | **follow-up**: silence the input to the decoder rather than the decoder itself |
| sham-01 … sham-24 | 24 random pairs of comparable, unrelated neurons | null: what does *any* two-neuron knockout do? |
| blank-vision / frozen-vision | nothing; receptors see black / the first frame forever | does output depend on the image? |

## How "specific" is decided

The model is deterministic, so there is no run-to-run noise to test against. The 24 shams take
that role. An effect counts as **specific** only if, **on all three stimuli**, it is **larger in
size than the largest effect of any sham**, with the same sign each time. Shams
(`select_shams.py`) are active at 15–45 Hz, have 300–900 outgoing connections and no external
input, and are neither one of the watched cell types nor directly wired into them. The picks use
a fixed seed.

Two disclosures about procedure:

- **The criterion was changed once after seeing results.** The first version was "outside the
  range of the shams". It flagged Dm17 and MeVPMe2, because all 24 shams happen to raise those
  cell types and the target knockouts don't. The size-based rule replaced it. Nothing that
  passes the final rule depended on the change: w-cHIN, DNp20, DNpe017 and PS278 pass both.
- **The sham rules were written after a 3-sham pilot** that used the same rate and connection
  criteria. The rule excluding cells wired into the watched types was added afterwards. The 24
  final pairs were drawn by seed and none was dropped or replaced.

## Results

Full tables: [`results/comparison.md`](results/comparison.md). Hop distances:
[`results/propagation.json`](results/propagation.json).

| Arm | Decoded behavior | Specific effects on the rest of the network | Synapses away |
|---|---|---|---|
| dnp20-off | turning → 0. Movement and firing unchanged | **none**: no other neuron's spike count changes | — |
| dnpe017-off | movement and firing → 0. Turning within sham range | **w-cHIN** (the 2 active cells go silent) | 1 |
| both-off | all output → 0 | **w-cHIN** only, identical to dnpe017-off | 1 |
| mevp9-off | all output → 0 | **DNp20, DNpe017, w-cHIN, PS278** | 1, 1, 2, 1 |

w-cHIN spikes in 120 s (control / knockout / sham range):

| | s1 | s2 | s3 |
|---|---|---|---|
| dnpe017-off | 1,472 → **0** (shams 1,438–1,513) | 1,457 → **0** (1,436–1,537) | 1,332 → **0** (1,317–1,413) |

### What this shows

1. **The knockout method works and is exactly reproducible.** Silenced cells never fire (asserted
   in code). Frames are identical in every run of a stimulus. Reruns on other machines are
   byte-identical.
2. **DNp20 off → no turning. DNpe017 off → no movement or firing. Both off → nothing.** These are
   **true by construction**, because the Doom controller reads its commands directly from these
   cells. They validate the setup and are not neuroscience findings.
3. **DNpe017 → w-cHIN is the one specific downstream effect of a decoder knockout.** It holds on
   all 3 stimuli, is 16–36× larger than any sham, and w-cHIN is a direct synaptic target.
4. **The upstream follow-up propagates exactly one or two synapses.** Silencing the two MeVP9
   cells silences their direct targets (DNp20, DNpe017, PS278), then DNpe017's target (w-cHIN).
   Nothing else passes the sham test.
5. **Nothing propagates far.** No knockout produced a specific effect more than two synapses
   away. The only other change is network-wide spike-timing reshuffling of about 8,100–8,300
   neurons. Shams cause the same amount, so it isn't specific to any target.

### What this does not show

- **"Silencing DNpe017 changes turning" does not hold up.** The first run suggested −1.3%. On all
  three stimuli the change sits inside the sham range.
- **Both-off adds nothing.** It is exactly DNp20-off plus DNpe017-off. The two pathways don't interact.
- **PS278 is weak evidence.** It is one cell firing 12–18 spikes per 120 s, which drops to 0.
  It passes the test, but the absolute numbers are tiny.

## Limitations

- **This is a simulated fly-brain intervention experiment, not a fly brain playing Doom.** The
  loop is open. The brain watches Doom frames (a seeded game with a scripted camera sweep, not
  recorded footage), and its commands are recorded but never applied. The player stands still and
  respawns about 20 times per run.
- **Only the visual system is active.** About 11,700 of 166,700 neurons fire. The central brain,
  the ventral nerve cord and the motor neurons are almost entirely silent.
- **Output depends only weakly on the image.** With a black screen the brain still turns (1.38°/tic),
  moves (6.95) and fires (44% of tics), driven by DOOMFLY's constant 12 mV lamina bias. A frozen
  frame gives nearly the same output as live video. The brain turns right on nearly every tic,
  even when the camera sweeps left.
- **The null distribution is 24 optic-lobe cells**, because those are the only active cells that
  qualify. Shams and targets are not interchangeable anatomically.
- **No run-to-run noise.** One connectome and deterministic dynamics. The shams stand in for
  noise, but this is not a statistical test on replicate animals.
- **Bit-exact only on the same platform.** Runs are byte-identical across our Linux Devboxes.
  Against the numbers DOOMFLY's author published from a Mac build, the same graph (identical
  sha256) gives spike totals within about 0.1%, not identical. Compiler and CPU floating-point
  differences get amplified by the network. Conclusions here rest on effects far larger than that.
- The blank and frozen controls are identical across stimuli (black is black, and all three
  seeds start from the same spawn view), so they are effectively one control run three times.
- LIF dynamics, inferred transmitter signs and an approximate retina mapping. See DOOMFLY's own
  [model review](https://github.com/nftechie/doomfly/blob/main/docs/doom-neuroscience-review.md).

## Provisioning the whole experiment with the Namespace SDK

`provision/provision.mjs` runs an entire experiment from one file, with no manual Devbox setup:

```sh
cd provision && npm install
node provision.mjs ../experiments/knockouts-100.json      # or repro-93.json; add --keep to leave the boxes up
```

It creates the Blueprint `fly-doomfly` if missing, creates the Devboxes in parallel from the
pre-baked image, spreads every (stimulus, condition) run across them, selects the sham pairs on the
box that ran the first control, runs the shams, pulls everything into `experiments/<name>/results/`,
runs `verify_results.py` and `compare.py` on it, and deletes the Devboxes, also after a failure.

| File | What it is |
|---|---|
| `experiments/*.json` | the whole design: stimuli, sham count and seed, run length, image, box size and count, runs per box |
| `provision/image/Dockerfile` | the Custom Image `fly/doomfly`: pinned DOOMFLY, the MaleCNS data (checksum-verified), the prepared graph and the native kernel, all under `/opt/fly`. Build with `devbox image build provision/image --name=fly/doomfly --user=devbox` (about 10 minutes) |
| `provision/smoke.mjs` | one-box check of the SDK path: blueprint, create, `fly-check`, a 3 s run, delete |

A Devbox from the image is ready to simulate about 13 seconds after creation; nothing is downloaded
or compiled per box. `run_batch.sh` reads the image's `FLY_DOOMFLY` / `FLY_VENV` paths, so the same
scripts run on hand-made boxes (`setup.sh`, under `/workspaces`) and on image-based ones.

One SDK detail: version 1.4.0 treats any image name containing `/` as a registry reference, so the
Blueprint is created with a placeholder image and its `imageName` is then set directly.

**Checked:** `experiments/repro-93` re-ran the whole 93-run experiment through the provisioner on one
Devbox created from the image (8 min for the 21 main runs, 26 min for the 72 shams). Every per-tic
value and every one of the 166,700 neuron counts in all 93 runs matched the original hand-run
results exactly, and the same 24 sham pairs were selected.

**100 simulated brains** (`experiments/knockouts-100`): 4 stimuli × (intact + 4 targeted knockouts + 2 vision
controls + 18 sham pairs) = 100 runs on 4 provisioned Devboxes, **12 min 48 s** from creating the boxes to deleting
them (boxes ready in 13 s, main runs 4 min, shams 8 min). Same conclusions as the 93-run experiment on a fourth
stimulus: DNp20 off removes turning; DNpe017 off removes movement and firing and silences w-cHIN; MeVP9 off removes
everything and silences DNp20, DNpe017, w-cHIN and PS278; no sham comes close.

**Account limit:** Namespace allows **10 Devboxes per user** on this account (`per-user devbox limit
reached (10)`), so a one-brain-per-box run of 100 needs the limit raised, or fewer, bigger boxes.

## Survival search (closed loop)

Can a small knockout make the simulated fly survive *longer* in Doom than the intact brain?
Here the brain plays the game: each tic's frame drives the brain, and the decoded TURN / MOVE / FIRE
commands move the player. Each candidate runs until it dies or reaches the time limit.

```sh
python3 run_survival_search.py --num-candidates 100 --knockout-size 2 --candidate-seed 42 \
    --game-seeds 1,2,3,4,5,6,7,41027 --max-tics 4200 --devboxes fly-control
python run_candidate.py --candidate-id 37 --neurons 48122,99102 --game-seed 1 --live-port 8900 --realtime
```

| File | What it does |
|---|---|
| `fly_sim.py` | shared core: load the brain, silence neurons (also used by `run_condition.py`) |
| `run_candidate.py` | one candidate on one game seed, fully independent. Writes one result JSON. `--live-port` serves `live.html` with the gameplay, timer, TURN/MOVE/FIRE and ALIVE/DEAD |
| `run_survival_search.py` | coordinator: generate candidates (fixed seed), assign to machines, run on Devboxes, collect, rank. Writes `manifest.json`, `results.csv`, `results.json` |

Candidates are drawn from the **1,341 neurons that fire in the control run and can be fully silenced**.
The other 10,336 active neurons are photoreceptors and lamina cells that receive direct input; cutting
their synapses would not stop them firing, so they are excluded. Candidate 0 is always the intact brain.

**First milestone** (`results/survival/milestone1*`, intact + 5 random pairs, run on one Devbox):

- Silenced neurons fired 0 spikes in every run; every run started from the same first frame.
- Death is detected at the tic the game reports the player dead. The MeVP9 pair dies after tic 182,
  matching the earlier demo run.
- Rerunning a candidate reproduced its result, per-tic trace and frame hash exactly.
- The intact brain dies on all 8 seeds, after 36 to 97 s (mean 66 s), so there is room to beat it.

**Full search** (`results/survival/k2-n100-c42-screen8` and `k2-top10-holdout8`, 6 provisioned Devboxes):
all 100 random pairs on 8 game seeds (808 runs), then the top 10 re-tested on 8 fresh seeds (88 runs).

| | Best pair | Pairs beating intact on every seed | Median ratio |
|---|---|---|---|
| One seed (41027) | 1.81x | 53 of 100 "won" | 1.02x |
| 8 seeds | 1.36x | 1 of 100 | 1.06x |
| Top 10 on 8 fresh seeds | 1.13x | 0 of 10 | 1.03x |

The screen's winners did not hold up: its best pair (1.36x) fell to 0.89x on fresh seeds, and the one
pair that beat intact on all 8 screening seeds scored 1.03x and won 3 of 8. **No 2-neuron knockout
reliably outlives the intact brain.** Random knockouts re-roll the game; selection then picks the
lucky ones. Every candidate kept moving (100% of tics) and firing (94%), so no degenerate "hide and
survive" strategy appeared either. The longest-lasting fly, within noise, is the intact one.

**Read rankings on one seed as luck.** On seed 1 alone, all 5 random pairs "beat" intact, by 1.45x to
2.12x. Seed 1 is simply intact's worst seed. On 8 seeds the same pairs score 0.95x to 1.15x, none beats
intact on every seed, and each wins on about half. Closed-loop games diverge from any small change, so
a knockout mostly re-rolls the dice. A real winner has to hold up across many seeds and then again on
fresh seeds it was not selected on. Two of the five pairs also reached the 120 s limit on one seed, so
a longer `--max-tics` is needed to avoid capping good runs.

## Demo page

`demo/index.html` is a silent, looping 10-second visualization for screen recording. Open it
directly in a browser; click or press R to restart.

Unlike the experiment (open loop), the demo footage is **closed loop**: the brain's decoded commands
drive the game, so each knockout plays differently. All four runs use the same seed and start from
the identical first frame; the knockout is the only difference. Over 10 s, the control survives with
0 deaths; DNpe017− and MeVP9− are killed at tic 183 and DNp20− at tic 311.

The footage, health, deaths, per-tic commands and decoder spike rasters on the page all come from
`results/closed-loop/<arm>/ticks.csv` (produced with `run_condition.py --closed-loop --dump-frames`
for 10 s). Frames are stored as 256×192 JPEG sprite sheets (`demo/closed-<arm>.jpg`). These four
runs were made on one Devbox, not four. The closed-loop runs are a demonstration only; none of the
specificity results above depend on them.

## Reproduce

```sh
./launch.sh 120     # creates/reuses 4 Devboxes, runs all 93 jobs, writes results/comparison.md
python3 compare.py  # re-run the comparison on downloaded results
```

| File | What it does |
|---|---|
| `setup.sh` | per box: pinned DOOMFLY `71ecf53`, Python 3.11, MaleCNS data (sha256-checked), graph + kernel |
| `run_condition.py` | one arm on one stimulus. Silences cells, asserts they never fire, writes per-tic output and all neuron counts |
| `run_batch.sh` | runs a job list 12 at a time on a box (0.5 GB and one core per run) |
| `select_shams.py` | picks the 24 sham pairs by fixed rules and seed. Exports cell-type labels |
| `compare.py` | checks frame hashes, applies the sham test, writes `results/comparison.{md,json}` |
| `propagation.py` | synaptic distance from each knockout to each specific effect (runs on a box) |
| `verify_results.py` | integrity checks on every result set: provenance, frame hashes, tick counts, silenced cells at zero |
| `audit_wiring.py` | the connectome queries behind the MeVP9 and w-cHIN wiring claims (runs on a box) |
| `conditions.json`, `stimuli.json`, `shams.json` | the arms, the 3 stimuli and the 24 sham pairs |

Each run writes `results/<stimulus>/<arm>/`: `summary.json` (behavior, rates and provenance,
including data and kernel hashes), `ticks.csv` (per-tic commands, decoder spikes and frame hash),
`neuron_counts.npz` (spikes per neuron after warm-up) and `celltype_spikes.json`.

Each run uses MaleCNS v1.0 wiring and one fixed stimulus, and measures decoded commands and neural
activity over 119 s of simulated time starting at t = 1 s. The first 35 tics are warm-up and are excluded.

## Next

- Close the loop: apply the decoded commands, and compare survival and kills across arms.
- Screen upstream systematically: silence each visual cell type in turn and rank them by effect on MeVP9.
- Add membrane noise so each arm gets real replicates and confidence intervals.

DOOMFLY is MIT licensed. The MaleCNS data are CC-BY 4.0 (Janelia/Google).
