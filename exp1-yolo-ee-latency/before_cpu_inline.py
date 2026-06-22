#!/usr/bin/env python3
"""
BEFORE run: CPU-inline YOLO inference inside the robot control loop.

Run in the lerobot conda env (Python 3.12):
    conda activate lerobot
    cd examples/anshul
    python before_cpu_inline.py

Logs: logs/before.csv
Footage: footage/before.mp4
"""

from __future__ import annotations

import os
import sys
import time
import traceback

import cv2
from ultralytics import YOLO

# Allow running from repo root or from examples/anshul
# common.py is the shared module at the anshul root (parent of this experiment folder)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import (  # noqa: E402
    DEFAULT_CONTROL_FREQ,
    DEFAULT_KP,
    DEFAULT_MODEL,
    DEFAULT_RUN_SECONDS,
    DEFAULT_TARGET_OBJECTS,
    EE_X0,
    EE_Y0,
    FOOTAGE_DIR,
    K_PAN,
    K_Y,
    LOGS_DIR,
    MetricsLogger,
    FootageRecorder,
    SSHKeyboardTeleop,
    apply_vision_offset,
    display_available,
    draw_metrics_overlay,
    ensure_output_dirs,
    keyboard_step,
    list_cameras,
    move_to_zero_position,
    return_to_start_position,
    send_p_control_action,
    setup_ssh_keyboard_if_needed,
)


def run_inline_vision(
    target_positions,
    current_x,
    current_y,
    model,
    cap,
    target_objects,
):
    """Run one inline CPU vision step; returns updated coords and timing fields."""
    ret, frame = cap.read()
    if not ret:
        print("Camera frame not available")
        return current_x, current_y, 0.0, False, None, None

    capture_ts = time.time()
    t0 = time.perf_counter()
    results = model(frame, verbose=False)
    infer_ms = (time.perf_counter() - t0) * 1000.0

    detected = False
    annotated_frame = frame

    if results and hasattr(results[0], "boxes") and results[0].boxes:
        annotated_frame = results[0].plot()
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
                current_x, current_y = apply_vision_offset(
                    target_positions, current_x, current_y, dx, dy
                )
                detected = True
                print(
                    f"{label.capitalize()} center offset: dx={dx}, dy={dy} -> "
                    f"pan: {target_positions['shoulder_pan']:.2f}, y: {current_y:.3f}"
                )
                break

    return current_x, current_y, infer_ms, detected, annotated_frame, capture_ts


def p_control_loop(
    robot,
    keyboard,
    target_positions,
    start_positions,
    current_x,
    current_y,
    model,
    cap,
    target_objects,
    metrics: MetricsLogger,
    recorder: FootageRecorder,
    run_seconds: int = DEFAULT_RUN_SECONDS,
    kp: float = DEFAULT_KP,
    control_freq: int = DEFAULT_CONTROL_FREQ,
    show_window: bool = False,
):
    control_period = 1.0 / control_freq
    pitch = 0.0
    pitch_step = 1.0
    start_t = time.time()
    last_infer_ms = 0.0
    last_e2e_ms = 0.0
    last_detected = False

    print(f"Starting BEFORE loop ({run_seconds}s), control frequency: {control_freq}Hz")
    if show_window:
        print("Live preview enabled — press 'q' in the camera window to stop early.")
    else:
        print("No GUI display — preview disabled; footage is still saved to mp4.")

    while time.time() - start_t < run_seconds:
        try:
            loop_t0 = time.time()

            current_x, current_y, infer_ms, detected, annotated, capture_ts = run_inline_vision(
                target_positions,
                current_x,
                current_y,
                model,
                cap,
                target_objects,
            )
            last_infer_ms = infer_ms
            last_detected = detected

            keyboard_action = keyboard.get_action()
            if keyboard_action:
                should_exit, current_x, current_y, pitch = keyboard_step(
                    keyboard_action, target_positions, current_x, current_y, pitch, pitch_step
                )
                if should_exit:
                    print("Exit command detected, returning to start position...")
                    return_to_start_position(robot, start_positions, 0.2, control_freq)
                    return

            if "shoulder_lift" in target_positions and "elbow_flex" in target_positions:
                target_positions["wrist_flex"] = (
                    -target_positions["shoulder_lift"] - target_positions["elbow_flex"] + pitch
                )

            send_p_control_action(robot, target_positions, kp)
            last_e2e_ms = (time.time() - capture_ts) * 1000.0 if capture_ts else 0.0

            loop_dt_ms = (time.time() - loop_t0) * 1000.0
            loop_hz = 1000.0 / loop_dt_ms if loop_dt_ms > 0 else 0.0
            metrics.log(
                infer_ms=last_infer_ms,
                e2e_latency_ms=last_e2e_ms,
                detected=last_detected,
                vision_update=True,
            )

            if annotated is not None:
                draw_metrics_overlay(
                    annotated,
                    last_infer_ms,
                    loop_hz,
                    last_e2e_ms,
                    metrics._vision_count / max(time.time() - metrics._vision_window_start, 1e-6),
                    "BEFORE (CPU inline)",
                )
                recorder.write(annotated)
                if show_window:
                    cv2.imshow("BEFORE YOLO Follow (CPU inline)", annotated)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        print("Quit requested from preview window")
                        break

            elapsed = time.time() - loop_t0
            if elapsed < control_period:
                time.sleep(control_period - elapsed)

        except KeyboardInterrupt:
            print("User interrupted program")
            break
        except Exception as e:
            print(f"P control loop error: {e}")
            traceback.print_exc()
            break

    print(f"BEFORE run complete ({run_seconds}s elapsed)")
    return_to_start_position(robot, start_positions, 0.2, control_freq)


def main():
    print("YOLO Follow Latency Experiment — BEFORE (CPU inline)")
    print("=" * 60)

    ensure_output_dirs()

    try:
        from lerobot.robots.so_follower.config_so_follower import SO100FollowerConfig
        from lerobot.robots.so_follower.so_follower import SO100Follower
        from lerobot.teleoperators.keyboard.configuration_keyboard import KeyboardTeleopConfig
        from lerobot.teleoperators.keyboard.teleop_keyboard import KeyboardTeleop

        port = input("Please enter SO100 robot USB port (e.g.: /dev/ttyACM0): ").strip()
        if not port:
            port = "/dev/ttyACM0"
            print(f"Using default port: {port}")

        robot_config = SO100FollowerConfig(port=port)
        robot = SO100Follower(robot_config)
        keyboard_config = KeyboardTeleopConfig()
        keyboard = KeyboardTeleop(keyboard_config)

        robot.connect()
        keyboard.connect()
        use_stdin_keyboard = setup_ssh_keyboard_if_needed(keyboard)
        print("Devices connected successfully!")

        while True:
            calibrate_choice = input("Do you want to recalibrate the robot? (y/n): ").strip().lower()
            if calibrate_choice in ["y", "yes"]:
                robot.calibrate()
                break
            if calibrate_choice in ["n", "no"]:
                break
            print("Please enter y or n")

        start_obs = robot.get_observation()
        start_positions = {}
        for key, value in start_obs.items():
            if key.endswith(".pos"):
                motor_name = key.removesuffix(".pos")
                start_positions[motor_name] = int(value)

        move_to_zero_position(robot)

        target_positions = {
            "shoulder_pan": 0.0,
            "shoulder_lift": 0.0,
            "elbow_flex": 0.0,
            "wrist_flex": 0.0,
            "wrist_roll": 0.0,
            "gripper": 0.0,
        }
        current_x, current_y = EE_X0, EE_Y0

        model = YOLO(DEFAULT_MODEL)
        print(f"Loaded model: {DEFAULT_MODEL} (CPU, inline in control loop)")

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

        if use_stdin_keyboard:
            keyboard = SSHKeyboardTeleop()
            keyboard.connect()

        metrics = MetricsLogger(LOGS_DIR / "before.csv")
        recorder = FootageRecorder(FOOTAGE_DIR / "before.mp4", fps=15.0, realtime=True)
        show_window = display_available()

        print(f"Logging to {metrics.csv_path}")
        print(f"Recording to {recorder.output_path}")
        print(f"Vision mapping: K_pan={K_PAN}, K_y={K_Y}")

        try:
            p_control_loop(
                robot,
                keyboard,
                target_positions,
                start_positions,
                current_x,
                current_y,
                model,
                cap,
                target_objects,
                metrics,
                recorder,
                run_seconds=run_seconds,
                show_window=show_window,
            )
        finally:
            metrics.close()
            recorder.close()
            cap.release()
            if show_window:
                cv2.destroyAllWindows()
            robot.disconnect()
            keyboard.disconnect()
            print("Program ended")

    except Exception as e:
        print(f"Program execution failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
