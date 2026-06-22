# YOLO End-Effector Follow: Latency Improvement Experiment

Reproducible before/after comparison for [examples/3_so100_yolo_ee_follow.py](../../3_so100_yolo_ee_follow.py).

## Quick start

### 1. BEFORE run (CPU inline, one process)

```bash
conda activate lerobot
cd examples/anshul/exp1-yolo-ee-latency
python before_cpu_inline.py
```

Outputs:
- `logs/before.csv`
- `footage/before.mp4`

### 2. AFTER run (GPU split, two processes)

**Important:** start the robot script first and wait until it prints
`UDP receiver listening`. When it prompts you, start the vision script.

**Terminal 1 — robot loop (lerobot env):**
```bash
conda activate lerobot
cd examples/anshul/exp1-yolo-ee-latency
python after_robot.py
```

Wait for `UDP receiver listening on 127.0.0.1:5005`, complete robot setup, then
when you see `Start after_vision_gpu.py in the other terminal now`, launch:

**Terminal 2 — GPU vision sidecar (yoloe-gpu env):**
```bash
conda activate yoloe-gpu
cd examples/anshul/exp1-yolo-ee-latency
python after_vision_gpu.py
```

Use the **same target object** and **same run duration** as the BEFORE run.

Outputs:
- `logs/after.csv`
- `footage/after.mp4`

### 3. Generate graphs

```bash
conda activate lerobot
cd examples/anshul/exp1-yolo-ee-latency
python plot_results.py
```

Outputs:
- `plots/infer_ms_comparison.png`
- `plots/loop_hz_over_time.png`
- `plots/e2e_latency_comparison.png`
- `plots/vision_fps_comparison.png`
- `logs/summary.md`

Then fill in measured numbers in [REPORT.md](./REPORT.md).

## Environment notes

| Component | Conda env | Python | CUDA |
| --- | --- | ---: | --- |
| Robot control + BEFORE vision | `lerobot` | 3.12 | not required |
| AFTER GPU vision | `yoloe-gpu` | 3.10 | required |

On Jetson, GPU PyTorch wheels are Python 3.10 only while lerobot needs 3.12 — that is why the AFTER run splits vision into a separate process (same pattern as [yoloe_segmentation_gpu.py](../../yoloe_segmentation_gpu.py)).

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `RUN_SECONDS` | `60` | Experiment duration |
| `YOLO_MODEL` | `yolo11x.pt` | Model weights (AFTER vision script) |

## Files

| File | Role |
| --- | --- |
| `../common.py` | Shared IK, P-control, metrics, UDP IPC (lives at the `anshul` root) |
| `before_cpu_inline.py` | BEFORE baseline (CPU inline YOLO) |
| `after_robot.py` | AFTER robot loop (UDP receiver) |
| `after_vision_gpu.py` | AFTER GPU vision (UDP sender + footage) |
| `plot_results.py` | Comparison graphs + summary table |
| `REPORT.md` | Written before/after report template |

## Run protocol

1. Move the same target object in front of the camera for both runs.
2. Keep run duration identical (default 60 s).
3. Do not change `K_pan` / `K_y` or P-control gains between runs.
4. Scripts auto return-to-start and exit when the timer elapses.
