# namespace-fly: which fly neurons change Doom behavior?

A controlled neural-intervention experiment on [DOOMFLY](https://github.com/nftechie/doomfly), a
simulation of the complete MaleCNS v1.0 fruit-fly connectome (166,700 neurons, 25,582,938
connections) wired to a Doom arena. A head agent spins up **four Namespace Devboxes**. Each runs the
same brain on the same Doom frames, with a different set of neurons silenced.

```text
                        HEAD AGENT (launch.sh)
                                 |
          +---------------+------+--------+---------------+
          v               v               v               v
     fly-control    fly-dnp20-off   fly-dnpe017-off   fly-both-off
          |               |               |               |
          +------ identical Doom frames (hash-verified) ---+
                                 |
                            compare.py
```

| Arm | Silenced | Question |
|---|---|---|
| control | none | Baseline |
| dnp20-off | DNp20 L+R (10162, 10059) | Does turning decrease? |
| dnpe017-off | DNpe017 L+R (10527, 555871) | Do forward movement and firing decrease? |
| both-off | all four | What remains? |

## Result (120 s per arm, open loop)

Full tables: [`results/comparison.md`](results/comparison.md).

| Arm | turn (mean abs, deg/tic) | forward | attack tics | other neurons changed |
|---|---|---|---|---|
| control | 1.792 | 18.81 | 90.6% | — |
| dnp20-off | **0** | 18.81 (identical) | 90.6% (identical) | **none** |
| dnpe017-off | 1.768 (**−1.3%**) | **0** | **0%** | **8,249** |
| both-off | **0** | **0** | **0%** | 8,249 |

1. **DNp20 is a dead end in this network.** Silencing it removes turning and leaves every other
   one of the 166,698 neurons spike-for-spike identical to control.
2. **DNpe017 is not a dead end.** Silencing it also silences all 14 **w-cHIN** cells
   (0.88 Hz → 0; DNpe017 is evidently their only effective driver). Small changes then spread to
   8,249 neurons, back into the optic lobe (Dm19 +0.12 Hz, Dm6, Dm1, L3, …) and into DNp20, whose
   rate falls 0.4%. **Turning drops 1.3%** although the controller never connects DNpe017 to turning.
3. Removing both leaves no decoded output. Neuron by neuron, the double knockout is exactly the
   sum of the two single-knockout effects. The only exceptions are the two DNp20 cells themselves,
   whose counts cannot go below zero. The two interventions do not interact.

### What this does and does not show

- Findings 1–3 in their first-order form (DNp20 off → no turning, etc.) are **true by construction**:
  DOOMFLY's controller reads turning from DNp20 and movement/fire from DNpe017. That part tests the
  engineered interface, not fly biology. The DOOMFLY authors say those mappings are engineering choices.
- The **off-target** effects (w-cHIN, the optic-lobe ripple, the 1.3% turning change) are the part
  that comes from the connectome itself. The effects are small, but they are exact. The model is
  deterministic and the stimulus is identical, so any nonzero difference is caused by the intervention.
  With no noise, the effect sizes carry no p-values. Adding noise and replicates is the next step
  for statistics.
- The baseline brain is close to saturated under this stimulus: it turns right on every tic,
  moves near max forward and fires on 91% of tics. The decoded behavior barely depends on what is on screen.
- LIF dynamics with inferred transmitter signs and an approximate retina mapping. This is not a
  validated fly. See DOOMFLY's own [model review](https://github.com/nftechie/doomfly/blob/main/docs/doom-neuroscience-review.md).

## Method

- **Stimulus**: ViZDoom `combat_survival`, seed 41027, with a scripted camera sweep of 2°/tic. The
  brain never moves the camera. The loop is **open**: commands are decoded and recorded, not applied.
  Each arm regenerates the frames, and `compare.py` refuses to run unless all 4,200 per-frame hashes
  match across arms.
- **Silencing**: every incoming and outgoing synapse of the target cells is set to weight 0.
  Descending neurons receive no external current, so they rest at −52 mV (below the −45 mV threshold)
  and cannot fire. The run asserts they emit zero spikes.
- **Window**: using MaleCNS v1.0 wiring and the fixed stimulus above, decoded commands are measured
  over 119 s of neural time, starting at t = 1 s. The first 35 tics are warm-up and are excluded.
- **Pinned**: DOOMFLY `71ecf53`, and the three MaleCNS files checked against DOOMFLY's sha256 lockfile.
  The kernel hash and data hashes are recorded in each `results/<arm>/summary.json`.
- **Cost**: each Devbox (size `l`, 16 vCPU / 32 GB) sets up in about 1 minute. The full graph runs at
  about 1.07× real time, so the whole experiment takes about 4 minutes of wall time.

## Reproduce

```sh
./launch.sh 120        # creates fly-* devboxes, sets up, runs all arms in parallel, compares
python3 compare.py     # re-run the comparison on downloaded results
```

`setup.sh` runs on each devbox. It clones pinned DOOMFLY, creates a Python 3.11 venv, downloads and
verifies the data, and builds the graph and kernel. `run_condition.py --condition <arm>` runs one arm.

Outputs per arm: `summary.json` (behavior, rates, provenance), `ticks.csv` (per-tic commands and
decoder spikes), `celltype_spikes.json` and `neuron_counts.npz` (spikes per neuron after warm-up).

## Next

Intervene **upstream**: silence visual-circuit cell types one at a time and rank them by how much
they move DNp20/DNpe017 activity. This asks which parts of the connectome drive the outputs, rather
than which output the controller happens to read.

DOOMFLY is MIT licensed. The MaleCNS data are CC-BY 4.0 (Janelia/Google).
