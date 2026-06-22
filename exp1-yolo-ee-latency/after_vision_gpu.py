#!/usr/bin/env python3
"""
AFTER run (vision half): GPU YOLO inference, UDP sender, annotated footage.

Run in the yoloe-gpu conda env (Python 3.10, CUDA):
    conda activate yoloe-gpu
    cd examples/anshul
    python after_vision_gpu.py

Sends detections to after_robot.py on UDP localhost:5005.
Footage: footage/after.mp4
"""

from __future__ import annotations

import os
import sys
import time

import cv2
import torch
from ultralytics import YOLO

# common.py is the shared module at the anshul root (parent of this experiment folder)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_RUN_SECONDS,
    DEFAULT_TARGET_OBJECTS,
    FOOTAGE_DIR,
    FootageRecorder,
    VisionUdpSender,
    display_available,
    draw_metrics_overlay,
    ensure_output_dirs,
    list_cameras,
)

MODEL_WEIGHTS = os.environ.get("YOLO_MODEL", DEFAULT_MODEL)


def main():
    print("YOLO Follow Latency Experiment — AFTER (GPU vision / UDP sender)")
    print("=" * 60)

    ensure_output_dirs()

    device = 0 if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: CUDA not available - running on CPU (slow).")
    else:
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")

    model = YOLO(MODEL_WEIGHTS)
    print(f"Loaded model: {MODEL_WEIGHTS}")

    target_input = input(
        "Enter objects to detect (comma-separated, e.g. bottle,cup,mouse): "
    ).strip()
    target_objects = DEFAULT_TARGET_OBJECTS if not target_input else [
        obj.strip() for obj in target_input.split(",") if obj.strip()
    ]
    print(f"Detection targets: {target_objects}")

    cameras = list_cameras()
    if not cameras:
        print("No cameras found!")
        return
    selected = int(input(f"Select camera index from {cameras}: "))
    cap = cv2.VideoCapture(selected)
    if not cap.isOpened():
        print("Camera not found!")
        return

    run_seconds = int(
        input(f"Run duration in seconds (default {DEFAULT_RUN_SECONDS}): ").strip()
        or DEFAULT_RUN_SECONDS
    )

    sender = VisionUdpSender()
    recorder = FootageRecorder(FOOTAGE_DIR / "after.mp4", fps=15.0, realtime=True)
    show_window = display_available()
    print(f"Recording to {recorder.output_path}")
    if show_window:
        print("Live preview enabled — press 'q' in the camera window to stop early.")
    else:
        print("No GUI display — preview disabled; footage is still saved to mp4.")
    print("Sending UDP packets to 127.0.0.1:5005")
    print(f"Running for {run_seconds}s (Ctrl+C to stop early)")

    seq = 0
    start_t = time.time()
    fps_t0 = time.time()
    fps_frames = 0
    vision_fps = 0.0
    last_infer_ms = 0.0
    last_send_print = 0.0

    try:
        while time.time() - start_t < run_seconds:
            ret, frame = cap.read()
            if not ret:
                print("Camera frame not available")
                continue

            capture_ts = time.time()
            t0 = time.perf_counter()
            results = model(frame, device=device, verbose=False)
            infer_ms = (time.perf_counter() - t0) * 1000.0
            last_infer_ms = infer_ms

            detected = False
            dx = dy = 0
            annotated = frame

            if results and hasattr(results[0], "boxes") and results[0].boxes:
                annotated = results[0].plot()
                for box in results[0].boxes:
                    cls = int(box.cls[0])
                    label = results[0].names[cls]
                    if label in target_objects:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2
                        h, w = frame.shape[:2]
                        dx = cx - w // 2
                        dy = cy - h // 2
                        detected = True
                        break

            seq += 1
            sender.send(seq, capture_ts, infer_ms, dx, dy, detected)

            now = time.time()
            if now - last_send_print >= 5.0:
                print(
                    f"UDP sent seq={seq}, detected={detected}, dx={dx}, dy={dy}, "
                    f"infer={infer_ms:.1f}ms"
                )
                last_send_print = now

            fps_frames += 1
            if fps_frames >= 10:
                vision_fps = fps_frames / (time.time() - fps_t0)
                fps_t0 = time.time()
                fps_frames = 0

            draw_metrics_overlay(
                annotated,
                last_infer_ms,
                vision_fps,
                last_infer_ms,
                vision_fps,
                "AFTER (GPU split)",
            )
            recorder.write(annotated)
            if show_window:
                cv2.imshow("AFTER YOLO Follow (GPU split)", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        sender.close()
        recorder.close()
        cap.release()
        if show_window:
            cv2.destroyAllWindows()
        print("Vision sidecar ended")


if __name__ == "__main__":
    main()
