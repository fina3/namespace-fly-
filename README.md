# namespace-fly: which fly neurons change Doom behavior?

A controlled neural-intervention experiment on [DOOMFLY](https://github.com/nftechie/doomfly), a
simulation of the MaleCNS v1.0 fruit-fly connectome (166,700 neurons, 25,582,938 connections)
wired to a Doom arena. A head agent spins up **four Namespace Devboxes**. Each runs the same brain
on the same Doom frames, with a different set of neurons silenced.

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

## Results (120 s per arm, open loop)

Full tables: [`results/comparison.md`](results/comparison.md).

### Main arms

| Arm | silenced | turn (deg/tic) | forward | attack tics |
|---|---|---|---|---|
| control | none | 1.792 | 18.81 | 90.6% |
| dnp20-off | DNp20 L+R (10162, 10059) | **0** | 18.81 | 90.6% |
| dnpe017-off | DNpe017 L+R (10527, 555871) | 1.768 | **0** | **0%** |
| both-off | all four | **0** | **0** | **0%** |

### Verification arms

| Arm | what it tests | result |
|---|---|---|
| control-rep | same run on a different machine | bit-identical to control, all 166,700 neurons |
| sham-a, -b, -c | knock out two unrelated optic-lobe cells | decoder output intact; **8,169–8,235 other neurons change**; turning shifts −0.0%, +1.4%, +0.2% |
| mevp9-off | knock out MeVP9 12764 + 12356, upstream of the decoder | turning, forward and attack all go to **0** |
| blank-vision | receptors see black | still turns 1.38, moves 6.95, attacks 43.9% of tics |
| frozen-vision | receptors see the first frame forever | turns 1.94, moves 17.17, attacks 84.2% |
| control-s2 / dnp20-off-s2 / dnpe017-off-s2 | different Doom seed and sweep direction | same pattern as the main arms |

## What is established

1. **The knockouts work and the runs are reproducible.** Silenced neurons fire zero spikes (asserted
   in code). Re-running on the same or a different machine gives byte-identical output.
2. **DNp20 off removes turning. DNpe017 off removes movement and firing.** This is **true by
   construction**: DOOMFLY's controller computes turning from DNp20 and movement/fire from DNpe017.
   It confirms the intervention, and it is not a discovery about flies.
3. **DNp20's downstream targets never fire in this model.** DNp20 has 73 output connections onto 71
   cells (mostly neck motor neurons), and none of those cells spikes in control. So silencing DNp20
   changes no other neuron's spike count.
4. **DNpe017 drives w-cHIN.** Two of the 14 w-cHIN cells fire in control (1,472 spikes). They stop
   completely when DNpe017 is silenced, in both stimuli. They keep firing in all three shams
   (1,455–1,460 spikes). DNpe017 supplies about 98% of their active excitatory drive.
5. **The decoder neurons are relays of two MeVP9 visual projection neurons.** MeVP9 12764 (40.0 Hz)
   and 12356 (25.0 Hz) supply essentially all active input to DNp20 and DNpe017. DNp20's spike count
   equals MeVP9's in every arm. Silencing those two cells removes all decoded behavior.

## What is NOT established

- **"Silencing DNpe017 perturbs 8,247 other neurons" is not specific to DNpe017.** Sham knockouts of
  unrelated cells perturb the same number (about 8,200). The network is deterministic and recurrent,
  so any small change reshuffles spike timing across the active optic-lobe population. The count
  measures sensitivity to perturbation, not DNpe017's wiring.
- **"Turning drops 1.3%" is within sham range.** Shams moved turning by up to 1.4%. DNp20 lost 30
  spikes with DNpe017 off and 32 in the second stimulus, against 2–11 in the shams. That is
  suggestive, but three shams are too few to call it an effect.
- **The double knockout being "additive" carries no information**, given that DNp20 off changes
  nothing else.

## Limits of the model that affect interpretation

- **Only the visual system is active.** 11,677 of 166,700 neurons fire at all. The central brain,
  the ventral nerve cord and the motor neurons are silent. "Whole-brain simulation" is accurate
  about what is loaded, not about what participates.
- **Behavior depends only weakly on the image.** With a black screen the brain still turns, moves
  and fires, driven by DOOMFLY's constant 12 mV lamina bias. A frozen frame gives nearly the same
  output as live video. The brain turns right on more than 99.9% of tics in both stimuli, including
  the second one, which sweeps the other way.
- **Open loop.** Commands are decoded and recorded, never applied to the game. The player stands
  still, gets killed and respawns (21 rounds in 120 s). All arms see the same frames for this reason.
- **No noise, no replicates, no p-values.** One connectome, deterministic dynamics. Shams are the
  only yardstick for what counts as a meaningful difference.
- LIF dynamics, inferred transmitter signs and an approximate retina mapping. See DOOMFLY's own
  [model review](https://github.com/nftechie/doomfly/blob/main/docs/doom-neuroscience-review.md).

## Method

- **Stimulus**: ViZDoom `combat_survival`, seed 41027, scripted camera sweep of 2°/tic (second
  stimulus: seed 7, −3°/tic). Each arm regenerates the frames. `compare.py` refuses to run unless
  every per-frame hash matches its control.
- **Silencing**: every incoming and outgoing synapse of the target cells is set to weight 0. The
  targets receive no external current, so they rest at −52 mV, below the −45 mV threshold.
- **Shams**: chosen with a fixed random seed from non-input neurons firing 15–45 Hz with 300–900
  output connections. Only optic-lobe cells meet that, so the shams sit upstream of the decoder.
- **Window**: using MaleCNS v1.0 wiring and the fixed stimulus, decoded commands are measured over
  119 s of neural time starting at t = 1 s. The first 35 tics are warm-up and are excluded.
- **Pinned**: DOOMFLY `71ecf53`, MaleCNS files checked against DOOMFLY's sha256 lockfile. Kernel and
  data hashes are recorded in each `results/<arm>/summary.json`.
- **Cost**: size `l` Devbox (16 vCPU / 32 GB), about 1 minute to set up, about 1.07× real time.

## Reproduce

```sh
./launch.sh 120        # 4 main arms on 4 devboxes in parallel, then compare
python3 compare.py     # re-run the comparison on downloaded results
```

Verification arms run the same way on any set-up devbox:

```sh
python run_condition.py --condition sham-a                                  # also sham-b, sham-c, mevp9-off, blank-vision, frozen-vision
python run_condition.py --condition control --tag control-s2 --seed 7 --sweep -3.0
```

`audit_wiring.py` holds the connectome queries behind findings 3–5. It runs on a devbox after
`setup.sh` and a control run.

## Next

- Add membrane noise and run 10+ seeds per arm, so that effects get confidence intervals.
- Run 20+ shams to build a proper null distribution for off-target effects.
- Replace spike-count diffs with rate changes averaged over noise seeds.
- Close the loop: apply the decoded commands, and compare survival time and kills across arms.
- Screen upstream: silence visual cell types one at a time and rank them by effect on MeVP9.

DOOMFLY is MIT licensed. The MaleCNS data are CC-BY 4.0 (Janelia/Google).
