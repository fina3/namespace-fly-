# Results: DOOMFLY descending-neuron suppression

## Stimulus: seed 41027, sweep 2.0 deg/tic

Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 41027, 2.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).

Identical game frames in all 11 arms: sha256 `839dfceddda5e5c6d9d138f52d13bdd6e231045bbaceb036cfea153ab075c366` (4200 frames, 3522 distinct, every per-frame hash matches). In the blank and frozen arms the game frames are the same but the receptors are fed black / the first frame.

### Decoded behavior

| Arm | silenced | mean abs turn (deg/tic) | Δ turn vs control | mean forward | attack tics |
|---|---|---|---|---|---|
| control | — | 1.7916 | +0.00% | 18.807 | 90.6% |
| control-rep | — | 1.7916 | +0.00% | 18.807 | 90.6% |
| dnp20-off | DNp20 10059, DNp20 10162 | 0.0000 | -100.00% | 18.807 | 90.6% |
| dnpe017-off | DNpe017 10527, DNpe017 555871 | 1.7680 | -1.32% | 0.000 | 0.0% |
| both-off | DNp20 10059, DNp20 10162, DNpe017 10527, DNpe017 555871 | 0.0000 | -100.00% | 0.000 | 0.0% |
| mevp9-off | MeVP9 12356, MeVP9 12764 | 0.0000 | -100.00% | 0.000 | 0.0% |
| sham-a | Dm6 13346, Dm20 23131 | 1.7916 | +0.00% | 18.785 | 90.3% |
| sham-b | Dm20 26982, Dm1 547692 | 1.8171 | +1.43% | 18.780 | 90.0% |
| sham-c | Dm6 12132, Dm6 15801 | 1.7951 | +0.20% | 18.756 | 89.9% |
| blank-vision | — | 1.3846 | -22.72% | 6.953 | 43.9% |
| frozen-vision | — | 1.9387 | +8.21% | 17.169 | 84.2% |

### Decoder neuron firing rates (Hz)

| Arm | DNp20_R_10059 | DNp20_L_10162 | DNpe017_L_10527 | DNpe017_R_555871 |
|---|---|---|---|---|
| control | 39.97 | 25.04 | 25.04 | 23.59 |
| control-rep | 39.97 | 25.04 | 25.04 | 23.59 |
| dnp20-off | 0.00 | 0.00 | 25.04 | 23.59 |
| dnpe017-off | 39.75 | 25.02 | 0.00 | 0.00 |
| both-off | 0.00 | 0.00 | 0.00 | 0.00 |
| mevp9-off | 0.00 | 0.00 | 0.00 | 0.00 |
| sham-a | 39.97 | 25.03 | 25.04 | 23.50 |
| sham-b | 40.06 | 24.92 | 24.92 | 23.57 |
| sham-c | 39.94 | 24.98 | 24.98 | 23.45 |
| blank-vision | 19.27 | 7.75 | 7.75 | 9.63 |
| frozen-vision | 37.70 | 21.54 | 21.54 | 21.51 |

### Rest of the network vs control (silenced neurons excluded)

| Arm | other neurons with changed spike count | sum of abs spike changes | total spikes Δ | DNp20 spikes | DNpe017 spikes | w-cHIN spikes | MeVP9 spikes |
|---|---|---|---|---|---|---|---|
| control | 0 | 0 | +0.000% | 7737 | 5787 | 1472 | 7737 |
| control-rep | 0 | 0 | +0.000% | 7737 | 5787 | 1472 | 7737 |
| dnp20-off | 0 | 0 | -0.013% | 0 | 5787 | 1472 | 7737 |
| dnpe017-off | 8,247 | 70,208 | -0.012% | 7707 | 0 | 0 | 7708 |
| both-off | 8,245 | 70,178 | -0.025% | 0 | 0 | 0 | 7708 |
| mevp9-off | 8,150 | 83,123 | -0.041% | 0 | 0 | 0 | 0 |
| sham-a | 8,235 | 89,460 | -0.002% | 7735 | 5777 | 1460 | 7735 |
| sham-b | 8,188 | 89,352 | +0.006% | 7732 | 5770 | 1455 | 7731 |
| sham-c | 8,169 | 125,297 | +0.017% | 7726 | 5763 | 1456 | 7725 |
| blank-vision | 11,783 | 41,274,529 | -46.134% | 3215 | 2068 | 0 | 3215 |
| frozen-vision | 11,448 | 7,361,781 | -1.712% | 7049 | 5123 | 1238 | 7050 |

## Stimulus: seed 7, sweep -3.0 deg/tic

Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 7, -3.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).

Identical game frames in all 3 arms: sha256 `f307b2df41ec594b76abce12f876ba34d6932556646b176824ffa29717f840f6` (4200 frames, 3337 distinct, every per-frame hash matches). In the blank and frozen arms the game frames are the same but the receptors are fed black / the first frame.

### Decoded behavior

| Arm | silenced | mean abs turn (deg/tic) | Δ turn vs control | mean forward | attack tics |
|---|---|---|---|---|---|
| control-s2 | — | 1.8298 | +0.00% | 18.774 | 90.0% |
| dnp20-off-s2 | DNp20 10059, DNp20 10162 | 0.0000 | -100.00% | 18.774 | 90.0% |
| dnpe017-off-s2 | DNpe017 10527, DNpe017 555871 | 1.7876 | -2.31% | 0.000 | 0.0% |

### Decoder neuron firing rates (Hz)

| Arm | DNp20_R_10059 | DNp20_L_10162 | DNpe017_L_10527 | DNpe017_R_555871 |
|---|---|---|---|---|
| control-s2 | 40.04 | 24.80 | 24.80 | 23.55 |
| dnp20-off-s2 | 0.00 | 0.00 | 24.80 | 23.55 |
| dnpe017-off-s2 | 39.73 | 24.84 | 0.00 | 0.00 |

### Rest of the network vs control (silenced neurons excluded)

| Arm | other neurons with changed spike count | sum of abs spike changes | total spikes Δ | DNp20 spikes | DNpe017 spikes | w-cHIN spikes | MeVP9 spikes |
|---|---|---|---|---|---|---|---|
| control-s2 | 0 | 0 | +0.000% | 7716 | 5754 | 1457 | 7715 |
| dnp20-off-s2 | 0 | 0 | -0.013% | 0 | 5754 | 1457 | 7715 |
| dnpe017-off-s2 | 8,118 | 71,038 | -0.012% | 7684 | 0 | 0 | 7684 |

## Where the activity is (control)

| Superclass | neurons | mean rate (Hz) |
|---|---|---|
| ol_sensory | 6,098 | 44.771 |
| ol_intrinsic | 89,403 | 2.491 |
| visual_centrifugal | 563 | 0.390 |
| descending_neuron | 1,314 | 0.086 |
| visual_projection | 9,201 | 0.010 |
| vnc_intrinsic | 13,161 | 0.001 |
| cb_intrinsic | 32,164 | 0.000 |
| all other superclasses | 14,796 | 0 (no spikes at all) |
