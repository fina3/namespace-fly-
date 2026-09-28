# Results: DOOMFLY knockout experiment

3 stimuli × (4 target knockouts + 24 sham knockouts + control + 2 vision controls) = 93 runs, 120 s each. Frame hashes match within every stimulus.

**Specific** = larger in size than the largest effect of any of the 24 shams, same direction, in every stimulus.

- **s1**: seed 41027, sweep 2.0°/tic, 3522 distinct frames, sha256 `839dfceddda5e5c6…`. Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 41027, 2.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).
- **s2**: seed 7, sweep -3.0°/tic, 3337 distinct frames, sha256 `f307b2df41ec594b…`. Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 7, -3.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).
- **s3**: seed 123, sweep 1.0°/tic, 3410 distinct frames, sha256 `535ca039b520540a…`. Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 123, 1.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).

## Decoded behavior and network change vs control

Δ turn in deg/tic, Δ forward in decoder units, Δ attack as a fraction of tics. Network columns exclude the knocked-out cells themselves.

### s1 (control: turn 1.792, forward 18.81, attack 0.906)

| Arm | turn_delta | forward_delta | attack_delta | other_neurons_changed | sum_abs_spike_change |
|---|---|---|---|---|---|
| **sham range** | -0.0900 … +0.0658 | -0.099 … +0.098 | -0.007 … +0.011 | 8,128 … 8,310 | 73,104 … 172,860 |
| dnp20-off | -1.7916 ◆ | +0.000 | +0.000 | 0 | 0 |
| dnpe017-off | -0.0236 | -18.807 ◆ | -0.906 ◆ | 8,247 | 70,208 |
| both-off | -1.7916 ◆ | -18.807 ◆ | -0.906 ◆ | 8,245 | 70,178 |
| mevp9-off | -1.7916 ◆ | -18.807 ◆ | -0.906 ◆ | 8,150 | 83,123 |
| blank-vision | -0.4070 ◆ | -11.854 ◆ | -0.467 ◆ | 11,783 ◆ | 41,274,529 ◆ |
| frozen-vision | +0.1471 ◆ | -1.638 ◆ | -0.064 ◆ | 11,448 ◆ | 7,361,781 ◆ |

### s2 (control: turn 1.830, forward 18.77, attack 0.900)

| Arm | turn_delta | forward_delta | attack_delta | other_neurons_changed | sum_abs_spike_change |
|---|---|---|---|---|---|
| **sham range** | -0.0954 … +0.0703 | -0.054 … +0.135 | -0.002 … +0.010 | 8,079 … 8,170 | 71,828 … 169,528 |
| dnp20-off | -1.8298 ◆ | +0.000 | +0.000 | 0 | 0 |
| dnpe017-off | -0.0422 | -18.774 ◆ | -0.900 ◆ | 8,118 | 71,038 |
| both-off | -1.8298 ◆ | -18.774 ◆ | -0.900 ◆ | 8,116 | 70,996 |
| mevp9-off | -1.8298 ◆ | -18.774 ◆ | -0.900 ◆ | 8,053 | 82,049 |
| blank-vision | -0.4452 ◆ | -11.822 ◆ | -0.461 ◆ | 11,781 ◆ | 41,019,702 ◆ |
| frozen-vision | +0.1089 ◆ | -1.606 ◆ | -0.058 ◆ | 11,407 ◆ | 6,999,124 ◆ |

### s3 (control: turn 1.716, forward 18.37, attack 0.894)

| Arm | turn_delta | forward_delta | attack_delta | other_neurons_changed | sum_abs_spike_change |
|---|---|---|---|---|---|
| **sham range** | -0.0535 … +0.0674 | +0.004 … +0.226 | -0.009 … +0.008 | 8,151 … 8,269 | 72,372 … 170,982 |
| dnp20-off | -1.7160 ◆ | +0.000 | +0.000 | 0 | 0 |
| dnpe017-off | -0.0241 | -18.369 ◆ | -0.894 ◆ | 8,153 | 71,262 |
| both-off | -1.7160 ◆ | -18.369 ◆ | -0.894 ◆ | 8,151 | 71,231 |
| mevp9-off | -1.7160 ◆ | -18.369 ◆ | -0.894 ◆ | 8,217 | 82,633 |
| blank-vision | -0.3314 ◆ | -11.416 ◆ | -0.455 ◆ | 11,802 ◆ | 39,551,296 ◆ |
| frozen-vision | +0.2227 ◆ | -1.200 ◆ | -0.052 ◆ | 11,482 ◆ | 7,309,234 ◆ |

◆ = larger in size than every sham on this stimulus.

## Specific effects (all stimuli, same direction)

### dnp20-off

- **turn_delta**: s1 -1.7916, s2 -1.8298, s3 -1.7160

0 cell types changed rate more than any sham, in every stimulus:


### dnpe017-off

- **forward_delta**: s1 -18.807, s2 -18.774, s3 -18.369
- **attack_delta**: s1 -0.906, s2 -0.900, s3 -0.894

1 cell types changed rate more than any sham, in every stimulus:

| Cell type | superclass | Δ Hz s1 (sham range) | Δ Hz s2 (sham range) | Δ Hz s3 (sham range) |
|---|---|---|---|---|
| w-cHIN | vnc_intrinsic | -0.884 (-0.020 … +0.025) | -0.875 (-0.013 … +0.048) | -0.800 (-0.009 … +0.049) |

### both-off

- **turn_delta**: s1 -1.7916, s2 -1.8298, s3 -1.7160
- **forward_delta**: s1 -18.807, s2 -18.774, s3 -18.369
- **attack_delta**: s1 -0.906, s2 -0.900, s3 -0.894

1 cell types changed rate more than any sham, in every stimulus:

| Cell type | superclass | Δ Hz s1 (sham range) | Δ Hz s2 (sham range) | Δ Hz s3 (sham range) |
|---|---|---|---|---|
| w-cHIN | vnc_intrinsic | -0.884 (-0.020 … +0.025) | -0.875 (-0.013 … +0.048) | -0.800 (-0.009 … +0.049) |

### mevp9-off

- **turn_delta**: s1 -1.7916, s2 -1.8298, s3 -1.7160
- **forward_delta**: s1 -18.807, s2 -18.774, s3 -18.369
- **attack_delta**: s1 -0.906, s2 -0.900, s3 -0.894

4 cell types changed rate more than any sham, in every stimulus:

| Cell type | superclass | Δ Hz s1 (sham range) | Δ Hz s2 (sham range) | Δ Hz s3 (sham range) |
|---|---|---|---|---|
| DNp20 | descending_neuron | -32.508 (-0.139 … +0.244) | -32.420 (-0.109 … +0.311) | -31.794 (-0.092 … +0.366) |
| DNpe017 | descending_neuron | -24.315 (-0.181 … +0.189) | -24.176 (-0.122 … +0.303) | -23.517 (-0.013 … +0.429) |
| w-cHIN | vnc_intrinsic | -0.884 (-0.020 … +0.025) | -0.875 (-0.013 … +0.048) | -0.800 (-0.009 … +0.049) |
| PS278 | cb_intrinsic | -0.071 (-0.017 … +0.029) | -0.076 (-0.029 … +0.008) | -0.050 (-0.025 … +0.017) |

## Watched cell types: total spikes

| Stimulus | Arm | DNp20 | DNpe017 | MeVP9 | w-cHIN |
|---|---|---|---|---|---|
| s1 | control | 7737 | 5787 | 7737 | 1472 |
| s1 | dnp20-off | 0 | 5787 | 7737 | 1472 |
| s1 | dnpe017-off | 7707 | 0 | 7708 | 0 |
| s1 | both-off | 0 | 0 | 7708 | 0 |
| s1 | mevp9-off | 0 | 0 | 0 | 0 |
| s1 | sham range | 7704 … 7795 | 5744 … 5832 | 7704 … 7795 | 1438 … 1513 |
| s2 | control | 7716 | 5754 | 7715 | 1457 |
| s2 | dnp20-off | 0 | 5754 | 7715 | 1457 |
| s2 | dnpe017-off | 7684 | 0 | 7684 | 0 |
| s2 | both-off | 0 | 0 | 7684 | 0 |
| s2 | mevp9-off | 0 | 0 | 0 | 0 |
| s2 | sham range | 7690 … 7790 | 5725 … 5826 | 7690 … 7790 | 1436 … 1537 |
| s3 | control | 7567 | 5597 | 7566 | 1332 |
| s3 | dnp20-off | 0 | 5597 | 7566 | 1332 |
| s3 | dnpe017-off | 7536 | 0 | 7536 | 0 |
| s3 | both-off | 0 | 0 | 7536 | 0 |
| s3 | mevp9-off | 0 | 0 | 0 | 0 |
| s3 | sham range | 7545 … 7654 | 5594 … 5699 | 7546 … 7655 | 1317 … 1413 |
