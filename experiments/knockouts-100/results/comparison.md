# Results: DOOMFLY knockout experiment

4 stimuli × (4 target knockouts + 18 sham knockouts + control + 2 vision controls) = 100 runs, 120 s each. Frame hashes match within every stimulus.

**Specific** = larger in size than the largest effect of any of the 24 shams, same direction, in every stimulus.

- **s1**: seed 41027, sweep 2°/tic, 3522 distinct frames, sha256 `839dfceddda5e5c6…`. Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 41027, 2.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).
- **s2**: seed 7, sweep -3°/tic, 3337 distinct frames, sha256 `f307b2df41ec594b…`. Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 7, -3.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).
- **s3**: seed 123, sweep 1°/tic, 3410 distinct frames, sha256 `535ca039b520540a…`. Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 123, 1.0 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).
- **s4**: seed 2026, sweep -1.5°/tic, 3412 distinct frames, sha256 `ceb530bb96cb06cc…`. Using MaleCNS v1.0 wiring and a fixed Doom stimulus (seed 2026, -1.5 deg/tic scripted sweep), measuring decoded commands over 119.000 s of neural time starting at t=1.000 s (first 35 tics are warm-up and excluded).

## Decoded behavior and network change vs control

Δ turn in deg/tic, Δ forward in decoder units, Δ attack as a fraction of tics. Network columns exclude the knocked-out cells themselves.

### s1 (control: turn 1.792, forward 18.81, attack 0.906)

| Arm | turn_delta | forward_delta | attack_delta | other_neurons_changed | sum_abs_spike_change |
|---|---|---|---|---|---|
| **sham range** | -0.0662 … +0.0373 | -0.079 … +0.114 | -0.006 … +0.005 | 8,179 … 8,285 | 76,910 … 149,579 |
| dnp20-off | -1.7916 ◆ | +0.000 | +0.000 | 0 | 0 |
| dnpe017-off | -0.0236 | -18.807 ◆ | -0.906 ◆ | 8,247 | 70,208 |
| both-off | -1.7916 ◆ | -18.807 ◆ | -0.906 ◆ | 8,245 | 70,178 |
| mevp9-off | -1.7916 ◆ | -18.807 ◆ | -0.906 ◆ | 8,150 | 83,123 |
| blank-vision | -0.4070 ◆ | -11.854 ◆ | -0.467 ◆ | 11,783 ◆ | 41,274,529 ◆ |
| frozen-vision | +0.1471 ◆ | -1.638 ◆ | -0.064 ◆ | 11,448 ◆ | 7,361,781 ◆ |

### s2 (control: turn 1.830, forward 18.77, attack 0.900)

| Arm | turn_delta | forward_delta | attack_delta | other_neurons_changed | sum_abs_spike_change |
|---|---|---|---|---|---|
| **sham range** | -0.0848 … +0.0025 | -0.046 … +0.160 | -0.001 … +0.015 | 8,108 … 8,195 | 75,855 … 150,597 |
| dnp20-off | -1.8298 ◆ | +0.000 | +0.000 | 0 | 0 |
| dnpe017-off | -0.0422 | -18.774 ◆ | -0.900 ◆ | 8,118 | 71,038 |
| both-off | -1.8298 ◆ | -18.774 ◆ | -0.900 ◆ | 8,116 | 70,996 |
| mevp9-off | -1.8298 ◆ | -18.774 ◆ | -0.900 ◆ | 8,053 | 82,049 |
| blank-vision | -0.4452 ◆ | -11.822 ◆ | -0.461 ◆ | 11,781 ◆ | 41,019,702 ◆ |
| frozen-vision | +0.1089 ◆ | -1.606 ◆ | -0.058 ◆ | 11,407 ◆ | 6,999,124 ◆ |

### s3 (control: turn 1.716, forward 18.37, attack 0.894)

| Arm | turn_delta | forward_delta | attack_delta | other_neurons_changed | sum_abs_spike_change |
|---|---|---|---|---|---|
| **sham range** | -0.0521 … +0.0216 | +0.008 … +0.257 | -0.006 … +0.009 | 8,184 … 8,313 | 77,037 … 149,320 |
| dnp20-off | -1.7160 ◆ | +0.000 | +0.000 | 0 | 0 |
| dnpe017-off | -0.0241 | -18.369 ◆ | -0.894 ◆ | 8,153 | 71,262 |
| both-off | -1.7160 ◆ | -18.369 ◆ | -0.894 ◆ | 8,151 | 71,231 |
| mevp9-off | -1.7160 ◆ | -18.369 ◆ | -0.894 ◆ | 8,217 | 82,633 |
| blank-vision | -0.3314 ◆ | -11.416 ◆ | -0.455 ◆ | 11,802 ◆ | 39,551,296 ◆ |
| frozen-vision | +0.2227 ◆ | -1.200 ◆ | -0.052 ◆ | 11,482 ◆ | 7,309,234 ◆ |

### s4 (control: turn 1.763, forward 18.67, attack 0.893)

| Arm | turn_delta | forward_delta | attack_delta | other_neurons_changed | sum_abs_spike_change |
|---|---|---|---|---|---|
| **sham range** | -0.0862 … +0.0095 | -0.076 … +0.102 | -0.001 … +0.018 | 8,127 … 8,278 | 76,555 … 151,041 |
| dnp20-off | -1.7630 ◆ | +0.000 | +0.000 | 0 | 0 |
| dnpe017-off | -0.0463 | -18.667 ◆ | -0.893 ◆ | 8,105 | 70,606 |
| both-off | -1.7630 ◆ | -18.667 ◆ | -0.893 ◆ | 8,103 | 70,559 |
| mevp9-off | -1.7630 ◆ | -18.667 ◆ | -0.893 ◆ | 8,162 | 82,900 |
| blank-vision | -0.3784 ◆ | -11.714 ◆ | -0.454 ◆ | 11,791 ◆ | 40,332,991 ◆ |
| frozen-vision | +0.1757 ◆ | -1.498 ◆ | -0.051 ◆ | 11,444 ◆ | 7,006,585 ◆ |

◆ = larger in size than every sham on this stimulus.

## Specific effects (all stimuli, same direction)

### dnp20-off

- **turn_delta**: s1 -1.7916, s2 -1.8298, s3 -1.7160, s4 -1.7630

0 cell types changed rate more than any sham, in every stimulus:


### dnpe017-off

- **forward_delta**: s1 -18.807, s2 -18.774, s3 -18.369, s4 -18.667
- **attack_delta**: s1 -0.906, s2 -0.900, s3 -0.894, s4 -0.893

1 cell types changed rate more than any sham, in every stimulus:

| Cell type | superclass | Δ Hz s1 (sham range) | Δ Hz s2 (sham range) | Δ Hz s3 (sham range) | Δ Hz s4 (sham range) |
|---|---|---|---|---|---|
| w-cHIN | vnc_intrinsic | -0.884 (-0.026 … -0.005) | -0.875 (-0.018 … +0.012) | -0.800 (-0.005 … +0.020) | -0.848 (-0.018 … +0.006) |

### both-off

- **turn_delta**: s1 -1.7916, s2 -1.8298, s3 -1.7160, s4 -1.7630
- **forward_delta**: s1 -18.807, s2 -18.774, s3 -18.369, s4 -18.667
- **attack_delta**: s1 -0.906, s2 -0.900, s3 -0.894, s4 -0.893

1 cell types changed rate more than any sham, in every stimulus:

| Cell type | superclass | Δ Hz s1 (sham range) | Δ Hz s2 (sham range) | Δ Hz s3 (sham range) | Δ Hz s4 (sham range) |
|---|---|---|---|---|---|
| w-cHIN | vnc_intrinsic | -0.884 (-0.026 … -0.005) | -0.875 (-0.018 … +0.012) | -0.800 (-0.005 … +0.020) | -0.848 (-0.018 … +0.006) |

### mevp9-off

- **turn_delta**: s1 -1.7916, s2 -1.8298, s3 -1.7160, s4 -1.7630
- **forward_delta**: s1 -18.807, s2 -18.774, s3 -18.369, s4 -18.667
- **attack_delta**: s1 -0.906, s2 -0.900, s3 -0.894, s4 -0.893

4 cell types changed rate more than any sham, in every stimulus:

| Cell type | superclass | Δ Hz s1 (sham range) | Δ Hz s2 (sham range) | Δ Hz s3 (sham range) | Δ Hz s4 (sham range) |
|---|---|---|---|---|---|
| DNp20 | descending_neuron | -32.508 (-0.088 … +0.319) | -32.420 (-0.080 … +0.324) | -31.794 (-0.080 … +0.366) | -32.181 (-0.118 … +0.311) |
| DNpe017 | descending_neuron | -24.315 (-0.185 … +0.256) | -24.176 (-0.118 … +0.307) | -23.517 (-0.004 … +0.471) | -23.983 (-0.109 … +0.269) |
| w-cHIN | vnc_intrinsic | -0.884 (-0.026 … -0.005) | -0.875 (-0.018 … +0.012) | -0.800 (-0.005 … +0.020) | -0.848 (-0.018 … +0.006) |
| PS278 | cb_intrinsic | -0.071 (-0.017 … +0.046) | -0.076 (-0.029 … +0.025) | -0.050 (-0.017 … +0.017) | -0.034 (-0.017 … +0.008) |

## Watched cell types: total spikes

| Stimulus | Arm | DNp20 | DNpe017 | MeVP9 | w-cHIN |
|---|---|---|---|---|---|
| s1 | control | 7737 | 5787 | 7737 | 1472 |
| s1 | dnp20-off | 0 | 5787 | 7737 | 1472 |
| s1 | dnpe017-off | 7707 | 0 | 7708 | 0 |
| s1 | both-off | 0 | 0 | 7708 | 0 |
| s1 | mevp9-off | 0 | 0 | 0 | 0 |
| s1 | sham range | 7716 … 7813 | 5743 … 5848 | 7716 … 7812 | 1428 … 1464 |
| s2 | control | 7716 | 5754 | 7715 | 1457 |
| s2 | dnp20-off | 0 | 5754 | 7715 | 1457 |
| s2 | dnpe017-off | 7684 | 0 | 7684 | 0 |
| s2 | both-off | 0 | 0 | 7684 | 0 |
| s2 | mevp9-off | 0 | 0 | 0 | 0 |
| s2 | sham range | 7697 … 7793 | 5726 … 5827 | 7697 … 7793 | 1427 … 1477 |
| s3 | control | 7567 | 5597 | 7566 | 1332 |
| s3 | dnp20-off | 0 | 5597 | 7566 | 1332 |
| s3 | dnpe017-off | 7536 | 0 | 7536 | 0 |
| s3 | both-off | 0 | 0 | 7536 | 0 |
| s3 | mevp9-off | 0 | 0 | 0 | 0 |
| s3 | sham range | 7548 … 7654 | 5596 … 5709 | 7548 … 7654 | 1323 … 1366 |
| s4 | control | 7659 | 5708 | 7660 | 1413 |
| s4 | dnp20-off | 0 | 5708 | 7660 | 1413 |
| s4 | dnpe017-off | 7632 | 0 | 7633 | 0 |
| s4 | both-off | 0 | 0 | 7633 | 0 |
| s4 | mevp9-off | 0 | 0 | 0 | 0 |
| s4 | sham range | 7631 … 7733 | 5682 … 5772 | 7631 … 7733 | 1383 … 1423 |
