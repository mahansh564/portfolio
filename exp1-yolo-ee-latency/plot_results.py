#!/usr/bin/env python3
"""
Generate before/after comparison graphs from experiment CSV logs.

Run after both experiment runs (lerobot env):
    conda activate lerobot
    cd examples/anshul
    python plot_results.py

Outputs:
    plots/summary_bars.png         <- headline: 4 metrics, log scale, speedup labels
    plots/infer_ms_comparison.png
    plots/e2e_latency_comparison.png
    plots/loop_hz_over_time.png
    plots/iterations_over_time.png <- cumulative loop iterations completed
    plots/vision_fps_comparison.png
    logs/summary.md

Notes on honesty / readability:
- The first logged sample of each run (loop_idx == 0) is a cold-start / model-load
  outlier (e.g. vision_fps ~ 460, infer_ms ~ 2.7-10.9 s). It is excluded from
  distribution plots and labeled as such, so a single warmup spike does not
  dominate the axes.
- BEFORE typically completes only a handful of loop iterations because each CPU
  inference blocks for ~10 s. We plot the actual individual points rather than a
  smooth violin built from 5 samples, and use log axes so the AFTER distribution
  stays visible next to the much larger BEFORE values.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# common.py is the shared module at the anshul root (parent of this experiment folder)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import LOGS_DIR, METRICS_FIELDS, PLOTS_DIR, ensure_output_dirs  # noqa: E402

BEFORE_CSV = LOGS_DIR / "before.csv"
AFTER_CSV = LOGS_DIR / "after.csv"
SUMMARY_MD = LOGS_DIR / "summary.md"

NUMERIC_COLS = ["infer_ms", "loop_dt_ms", "loop_hz", "e2e_latency_ms", "vision_fps"]

BEFORE_LABEL = "BEFORE (CPU inline)"
AFTER_LABEL = "AFTER (GPU split)"
BEFORE_COLOR = "#d62728"  # red = slow baseline
AFTER_COLOR = "#2ca02c"  # green = improved


def load_run(path: Path, label: str) -> dict[str, np.ndarray]:
    if not path.exists():
        raise FileNotFoundError(f"Missing log file: {path} (run the {label} experiment first)")

    columns: dict[str, list] = {field: [] for field in METRICS_FIELDS}
    columns["run"] = []

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in METRICS_FIELDS:
                if field in ("loop_idx", "detected"):
                    columns[field].append(int(float(row[field])))
                elif field == "wall_t":
                    columns[field].append(float(row[field]))
                else:
                    columns[field].append(float(row[field]))
            columns["run"].append(label)

    return {key: np.asarray(values) for key, values in columns.items()}


def drop_warmup(data: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Drop the cold-start sample (loop_idx == 0) that holds model-load / warmup outliers."""
    mask = data["loop_idx"] != 0
    if not mask.any():
        return data
    return {key: value[mask] for key, value in data.items()}


def positive(values: np.ndarray) -> np.ndarray:
    return values[values > 0]


def speedup_text(before: float, after: float, lower_is_better: bool) -> str:
    """Human-readable speedup/throughput factor between two scalar metrics."""
    if before <= 0 or after <= 0:
        return ""
    factor = (before / after) if lower_is_better else (after / before)
    if factor >= 100:
        return f"{factor:.0f}x"
    return f"{factor:.1f}x"


def annotate_bars(ax, rects, values, fmt):
    for rect, value in zip(rects, values, strict=True):
        ax.annotate(
            fmt.format(value),
            xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )


def summarize(data: dict[str, np.ndarray], label: str) -> dict[str, float]:
    warm = drop_warmup(data)
    detected_mask = warm["detected"] == 1
    infer = warm["infer_ms"][detected_mask] if detected_mask.any() else warm["infer_ms"]
    e2e = warm["e2e_latency_ms"][detected_mask] if detected_mask.any() else warm["e2e_latency_ms"]
    infer = positive(infer)
    e2e = positive(e2e)
    loop_hz = positive(warm["loop_hz"])
    vision_fps = positive(warm["vision_fps"])

    return {
        "run": label,
        "samples": int(len(data["loop_idx"])),
        "infer_ms_median": float(np.nanmedian(infer)) if infer.size else 0.0,
        "infer_ms_p95": float(np.nanpercentile(infer, 95)) if infer.size else 0.0,
        "loop_hz_median": float(np.nanmedian(loop_hz)) if loop_hz.size else 0.0,
        "loop_hz_p95": float(np.nanpercentile(loop_hz, 95)) if loop_hz.size else 0.0,
        "e2e_ms_median": float(np.nanmedian(e2e)) if e2e.size else 0.0,
        "e2e_ms_p95": float(np.nanpercentile(e2e, 95)) if e2e.size else 0.0,
        "vision_fps_median": float(np.nanmedian(vision_fps)) if vision_fps.size else 0.0,
        "vision_fps_p95": float(np.nanpercentile(vision_fps, 95)) if vision_fps.size else 0.0,
    }


def plot_summary_bars(before_s: dict[str, float], after_s: dict[str, float], out: Path) -> None:
    """Headline figure: the four key metrics as paired bars with speedup callouts."""
    metrics = [
        ("YOLO inference", "infer_ms_median", "ms", True, True),
        ("End-to-end latency", "e2e_ms_median", "ms", True, True),
        ("Control loop rate", "loop_hz_median", "Hz", False, True),
        ("Vision throughput", "vision_fps_median", "det/s", False, True),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    for ax, (title, key, unit, lower_is_better, log_scale) in zip(axes, metrics, strict=True):
        b = before_s[key]
        a = after_s[key]
        rects = ax.bar(
            [BEFORE_LABEL, AFTER_LABEL],
            [b, a],
            color=[BEFORE_COLOR, AFTER_COLOR],
            width=0.6,
        )
        if log_scale and b > 0 and a > 0:
            ax.set_yscale("log")
        annotate_bars(ax, rects, [b, a], "{:.1f}")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_ylabel(unit)
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(True, axis="y", alpha=0.3)
        ax.margins(y=0.25)

        factor = speedup_text(b, a, lower_is_better)
        if factor:
            verb = "lower" if lower_is_better else "higher"
            ax.text(
                0.5,
                0.92,
                f"{factor} {verb}",
                transform=ax.transAxes,
                ha="center",
                va="top",
                fontsize=13,
                fontweight="bold",
                color=AFTER_COLOR,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=AFTER_COLOR, alpha=0.9),
            )

    fig.suptitle(
        "GPU vision split vs CPU inline baseline (median, warmup excluded)",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out, dpi=150)
    plt.close(fig)


def _distribution_axes(ax, before_vals, after_vals, log_scale: bool) -> None:
    """Box plot per run with the raw points overlaid (honest about tiny BEFORE n)."""
    series = [before_vals, after_vals]
    positions = [1, 2]
    colors = [BEFORE_COLOR, AFTER_COLOR]

    bp = ax.boxplot(
        series,
        positions=positions,
        widths=0.5,
        showfliers=False,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=1.5),
    )
    for patch, color in zip(bp["boxes"], colors, strict=True):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)

    rng = np.random.default_rng(0)
    for pos, vals, color in zip(positions, series, colors, strict=True):
        if not len(vals):
            continue
        jitter = rng.uniform(-0.08, 0.08, size=len(vals))
        ax.scatter(
            np.full(len(vals), pos) + jitter,
            vals,
            s=18,
            color=color,
            edgecolor="white",
            linewidth=0.4,
            alpha=0.5,
            zorder=3,
        )

    if log_scale:
        ax.set_yscale("log")
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [f"{BEFORE_LABEL}\nn={len(before_vals)}", f"{AFTER_LABEL}\nn={len(after_vals)}"]
    )
    ax.grid(True, axis="y", alpha=0.3)


def plot_infer_ms(before: dict[str, np.ndarray], after: dict[str, np.ndarray], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    b = positive(drop_warmup(before)["infer_ms"])
    a = positive(drop_warmup(after)["infer_ms"])
    _distribution_axes(ax, b, a, log_scale=True)
    ax.set_ylabel("Inference time (ms, log scale)")
    ax.set_title("YOLO inference latency (warmup excluded)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_e2e_latency(before: dict[str, np.ndarray], after: dict[str, np.ndarray], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    b = positive(drop_warmup(before)["e2e_latency_ms"])
    a = positive(drop_warmup(after)["e2e_latency_ms"])
    _distribution_axes(ax, b, a, log_scale=True)
    ax.set_ylabel("End-to-end latency (ms, log scale)")
    ax.set_title("Capture \u2192 send_action latency (warmup excluded)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_loop_hz(before: dict[str, np.ndarray], after: dict[str, np.ndarray], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    b = drop_warmup(before)
    a = drop_warmup(after)
    tb = b["wall_t"] - b["wall_t"][0]
    ta = a["wall_t"] - a["wall_t"][0]

    ax.plot(ta, a["loop_hz"], color=AFTER_COLOR, label=AFTER_LABEL, alpha=0.85, linewidth=1.2)
    # BEFORE has very few, very low points: draw them as visible markers, not an invisible line.
    ax.plot(
        tb,
        b["loop_hz"],
        color=BEFORE_COLOR,
        label=BEFORE_LABEL,
        marker="o",
        markersize=6,
        linewidth=1.2,
    )
    ax.axhline(50, color="gray", linestyle="--", linewidth=1, label="50 Hz target")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Control loop rate (Hz, symlog)")
    ax.set_title("Control loop rate over time")

    b_med = float(np.nanmedian(positive(b["loop_hz"]))) if positive(b["loop_hz"]).size else 0.0
    a_med = float(np.nanmedian(positive(a["loop_hz"]))) if positive(a["loop_hz"]).size else 0.0
    ax.annotate(
        f"BEFORE \u2248 {b_med:.2f} Hz ({len(tb)} iterations total)",
        xy=(tb[-1] if len(tb) else 0, max(b_med, 0.1)),
        xytext=(0.35, 0.25),
        textcoords="axes fraction",
        color=BEFORE_COLOR,
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color=BEFORE_COLOR, alpha=0.7),
    )
    ax.text(
        0.98,
        0.92,
        f"AFTER \u2248 {a_med:.1f} Hz",
        transform=ax.transAxes,
        ha="right",
        va="top",
        color=AFTER_COLOR,
        fontsize=11,
        fontweight="bold",
    )
    ax.legend(loc="center right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_iterations_over_time(
    before: dict[str, np.ndarray], after: dict[str, np.ndarray], out: Path
) -> None:
    """Cumulative control-loop iterations completed: the clearest 'stall vs flow' story."""
    fig, ax = plt.subplots(figsize=(10, 5))
    tb = before["wall_t"] - before["wall_t"][0]
    ta = after["wall_t"] - after["wall_t"][0]
    ax.step(tb, np.arange(1, len(tb) + 1), where="post", color=BEFORE_COLOR, label=BEFORE_LABEL)
    ax.step(ta, np.arange(1, len(ta) + 1), where="post", color=AFTER_COLOR, label=AFTER_LABEL)
    ax.scatter(tb, np.arange(1, len(tb) + 1), color=BEFORE_COLOR, s=20, zorder=3)
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Control loop iterations completed")
    ax.set_title("Loop iterations completed over time")
    ax.text(
        0.98,
        0.6,
        f"AFTER: {len(ta)} iterations\nBEFORE: {len(tb)} iterations",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9),
    )
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_vision_fps(before: dict[str, np.ndarray], after: dict[str, np.ndarray], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    b = drop_warmup(before)
    a = drop_warmup(after)
    tb = b["wall_t"] - b["wall_t"][0]
    ta = a["wall_t"] - a["wall_t"][0]
    ax.plot(ta, a["vision_fps"], color=AFTER_COLOR, label=AFTER_LABEL, alpha=0.85, linewidth=1.2)
    ax.plot(
        tb,
        b["vision_fps"],
        color=BEFORE_COLOR,
        label=BEFORE_LABEL,
        marker="o",
        markersize=6,
        linewidth=1.2,
    )
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Vision throughput (detections/s)")
    ax.set_title("Vision FPS over time (warmup spike excluded)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def write_summary(rows: list[dict[str, float]], out: Path) -> None:
    lines = [
        "# Experiment summary",
        "",
        "Warmup sample (loop_idx == 0) excluded from medians/percentiles.",
        "",
        "| Run | Samples | infer ms (median) | infer ms (p95) | loop Hz (median) | "
        "e2e ms (median) | e2e ms (p95) | vision FPS (median) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['run']} | {row['samples']} | "
            f"{row['infer_ms_median']:.1f} | {row['infer_ms_p95']:.1f} | "
            f"{row['loop_hz_median']:.1f} | {row['e2e_ms_median']:.1f} | "
            f"{row['e2e_ms_p95']:.1f} | {row['vision_fps_median']:.2f} |"
        )

    if len(rows) == 2:
        before_s, after_s = rows
        lines.extend(
            [
                "",
                "## Improvement (AFTER vs BEFORE)",
                "",
                "| Metric | Factor |",
                "| --- | ---: |",
                f"| Inference latency | {speedup_text(before_s['infer_ms_median'], after_s['infer_ms_median'], True)} lower |",
                f"| End-to-end latency | {speedup_text(before_s['e2e_ms_median'], after_s['e2e_ms_median'], True)} lower |",
                f"| Control loop rate | {speedup_text(before_s['loop_hz_median'], after_s['loop_hz_median'], False)} higher |",
                f"| Vision throughput | {speedup_text(before_s['vision_fps_median'], after_s['vision_fps_median'], False)} higher |",
            ]
        )

    lines.extend(["", "Generated by `plot_results.py`."])
    out.write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_output_dirs()
    before = load_run(BEFORE_CSV, "before")
    after = load_run(AFTER_CSV, "after")

    before_s = summarize(before, "before")
    after_s = summarize(after, "after")

    plot_summary_bars(before_s, after_s, PLOTS_DIR / "summary_bars.png")
    plot_infer_ms(before, after, PLOTS_DIR / "infer_ms_comparison.png")
    plot_e2e_latency(before, after, PLOTS_DIR / "e2e_latency_comparison.png")
    plot_loop_hz(before, after, PLOTS_DIR / "loop_hz_over_time.png")
    plot_iterations_over_time(before, after, PLOTS_DIR / "iterations_over_time.png")
    plot_vision_fps(before, after, PLOTS_DIR / "vision_fps_comparison.png")

    write_summary([before_s, after_s], SUMMARY_MD)

    print("Wrote plots:")
    for name in [
        "summary_bars.png",
        "infer_ms_comparison.png",
        "e2e_latency_comparison.png",
        "loop_hz_over_time.png",
        "iterations_over_time.png",
        "vision_fps_comparison.png",
    ]:
        print(f"  {PLOTS_DIR / name}")
    print(f"Wrote summary: {SUMMARY_MD}")


if __name__ == "__main__":
    main()
