# Results: DOOMFLY descending-neuron suppression

Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 41027, 2.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).

Identical stimulus in all 4 arms: sha256 `839dfceddda5e5c6d9d138f52d13bdd6e231045bbaceb036cfea153ab075c366` (4200 frames, every per-frame hash matches).

## Decoded behavior (post warm-up)

| Arm | mean abs turn (deg/tic) | turning tics | mean forward | forward tics | attack tics |
|---|---|---|---|---|---|
| control | 1.792 | 100.0% | 18.807 | 100.0% | 90.6% |
| dnp20-off | 0.000 | 0.0% | 18.807 | 100.0% | 90.6% |
| dnpe017-off | 1.768 | 100.0% | 0.000 | 0.0% | 0.0% |
| both-off | 0.000 | 0.0% | 0.000 | 0.0% | 0.0% |

## Decoder neuron firing rates (Hz)

| Arm | DNp20_R_10059 | DNp20_L_10162 | DNpe017_L_10527 | DNpe017_R_555871 |
|---|---|---|---|---|
| control | 39.97 | 25.04 | 25.04 | 23.59 |
| dnp20-off | 0.00 | 0.00 | 25.04 | 23.59 |
| dnpe017-off | 39.75 | 25.02 | 0.00 | 0.00 |
| both-off | 0.00 | 0.00 | 0.00 | 0.00 |

## Rest of the network vs control

| Arm | total spikes Δ | neurons with changed spike count | first diverging tic | mean rate (Hz) |
|---|---|---|---|---|
| control | +0.000% | 0 of 166,700 | never | 2.9766 |
| dnp20-off | -0.013% | 2 of 166,700 | 1 | 2.9762 |
| dnpe017-off | -0.012% | 8,249 of 166,700 | 1 | 2.9762 |
| both-off | -0.025% | 8,249 of 166,700 | 1 | 2.9758 |

### dnp20-off: cell types with the largest rate change (silenced types excluded)

No cell type outside the silenced set changed rate.

### dnpe017-off: cell types with the largest rate change (silenced types excluded)

| Cell type | neurons | control Hz | arm Hz | Δ Hz |
|---|---|---|---|---|
| w-cHIN | 14 | 0.884 | 0.000 | -0.884 |
| DNp20 | 2 | 32.508 | 32.382 | -0.126 |
| Dm19 | 30 | 98.387 | 98.511 | +0.124 |
| Dm6 | 62 | 36.733 | 36.693 | -0.040 |
| Dm17 | 8 | 67.751 | 67.722 | -0.029 |
| Dm1 | 80 | 34.942 | 34.969 | +0.027 |
| Dm18 | 58 | 86.122 | 86.100 | -0.022 |
| Dm4 | 99 | 28.090 | 28.111 | +0.021 |
| MeVP9 | 12 | 5.418 | 5.398 | -0.020 |
| Dm13 | 53 | 64.098 | 64.080 | -0.018 |
| aMe30 | 5 | 43.867 | 43.882 | +0.015 |
| Dm20 | 98 | 55.632 | 55.623 | -0.009 |
| PS278 | 2 | 0.071 | 0.063 | -0.008 |
| L3 | 1772 | 29.696 | 29.703 | +0.008 |
| Dm12 | 276 | 28.335 | 28.329 | -0.006 |

### both-off: cell types with the largest rate change (silenced types excluded)

| Cell type | neurons | control Hz | arm Hz | Δ Hz |
|---|---|---|---|---|
| w-cHIN | 14 | 0.884 | 0.000 | -0.884 |
| Dm19 | 30 | 98.387 | 98.511 | +0.124 |
| Dm6 | 62 | 36.733 | 36.693 | -0.040 |
| Dm17 | 8 | 67.751 | 67.722 | -0.029 |
| Dm1 | 80 | 34.942 | 34.969 | +0.027 |
| Dm18 | 58 | 86.122 | 86.100 | -0.022 |
| Dm4 | 99 | 28.090 | 28.111 | +0.021 |
| MeVP9 | 12 | 5.418 | 5.398 | -0.020 |
| Dm13 | 53 | 64.098 | 64.080 | -0.018 |
| aMe30 | 5 | 43.867 | 43.882 | +0.015 |
| Dm20 | 98 | 55.632 | 55.623 | -0.009 |
| PS278 | 2 | 0.071 | 0.063 | -0.008 |
| L3 | 1772 | 29.696 | 29.703 | +0.008 |
| Dm12 | 276 | 28.335 | 28.329 | -0.006 |
| ME_unclear | 26 | 0.485 | 0.490 | +0.005 |
