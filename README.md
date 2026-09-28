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
