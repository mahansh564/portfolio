#!/usr/bin/env python3
"""
AFTER run (robot half): reads GPU vision detections over UDP, same control law.

Run in the lerobot conda env (Python 3.12):
    conda activate lerobot
    cd examples/anshul
    python after_robot.py

Start after_vision_gpu.py in the other terminal once you see
"UDP receiver listening" (yoloe-gpu env).

Logs: logs/after.csv
"""

from __future__ import annotations

import os
import sys
import time
import traceback

# common.py is the shared module at the anshul root (parent of this experiment folder)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import (  # noqa: E402
    DEFAULT_CONTROL_FREQ,
    DEFAULT_KP,
    DEFAULT_RUN_SECONDS,
    EE_X0,
    EE_Y0,
    LOGS_DIR,
    UDP_PORT,
    MetricsLogger,
    SSHKeyboardTeleop,
    VisionUdpReceiver,
    apply_vision_offset,
    keyboard_step,
    move_to_zero_position,
    return_to_start_position,
    send_p_control_action,
    setup_ssh_keyboard_if_needed,
    wait_for_first_udp_packet,
)


def p_control_loop(
    robot,
    keyboard,
    target_positions,
    start_positions,
    current_x,
    current_y,
    receiver: VisionUdpReceiver,
    metrics: MetricsLogger,
    run_seconds: int = DEFAULT_RUN_SECONDS,
    kp: float = DEFAULT_KP,
    control_freq: int = DEFAULT_CONTROL_FREQ,
):
    control_period = 1.0 / control_freq
    pitch = 0.0
    pitch_step = 1.0
    start_t = time.time()
    last_status_print = 0.0
    last_applied_seq = -1

    print(f"Starting AFTER robot loop ({run_seconds}s)")
    print(f"UDP packets received so far: {receiver.total_packets}")

    while time.time() - start_t < run_seconds:
        try:
            packet = receiver.poll()
            infer_ms = 0.0
            e2e_ms = 0.0
            detected = False
            vision_update = False

            if packet is not None:
                infer_ms = packet.infer_ms
                vision_update = True
                if packet.detected:
                    current_x, current_y = apply_vision_offset(
                        target_positions, current_x, current_y, packet.dx, packet.dy
                    )
                    detected = True
                    if packet.seq != last_applied_seq:
                        last_applied_seq = packet.seq
                        print(
                            f"UDP vision seq={packet.seq}: dx={packet.dx}, dy={packet.dy}, "
                            f"infer={packet.infer_ms:.1f}ms -> "
                            f"pan={target_positions['shoulder_pan']:.2f}, y={current_y:.3f}"
                        )
                elif packet.seq != last_applied_seq:
                    last_applied_seq = packet.seq
                    print(f"UDP seq={packet.seq}: no target detected")

            now = time.time()
            if now - last_status_print >= 5.0:
                latest = receiver.peek_latest()
                latest_seq = latest.seq if latest else "-"
                print(
                    f"UDP status: total={receiver.total_packets}, latest_seq={latest_seq}, "
                    f"vision_fps={receiver.vision_fps:.1f}"
                )
                last_status_print = now

            if "shoulder_lift" in target_positions and "elbow_flex" in target_positions:
                target_positions["wrist_flex"] = (
                    -target_positions["shoulder_lift"] - target_positions["elbow_flex"] + pitch
                )

            send_p_control_action(robot, target_positions, kp)

            if packet is not None and packet.detected:
                e2e_ms = (time.time() - packet.capture_ts) * 1000.0

            metrics.log(
                infer_ms=infer_ms,
                e2e_latency_ms=e2e_ms,
                detected=detected,
                vision_update=vision_update,
            )

            keyboard_action = keyboard.get_action()
            if keyboard_action:
                should_exit, current_x, current_y, pitch = keyboard_step(
                    keyboard_action, target_positions, current_x, current_y, pitch, pitch_step
                )
                if should_exit:
                    print("Exit command detected, returning to start position...")
                    return_to_start_position(robot, start_positions, 0.2, control_freq)
                    return

            time.sleep(control_period)

        except KeyboardInterrupt:
            print("User interrupted program")
            break
        except Exception as e:
            print(f"P control loop error: {e}")
            traceback.print_exc()
            break

    print(f"AFTER robot run complete ({run_seconds}s elapsed)")
    return_to_start_position(robot, start_positions, 0.2, control_freq)


def main():
    print("YOLO Follow Latency Experiment — AFTER (robot / UDP receiver)")
    print("=" * 60)

    try:
        receiver = VisionUdpReceiver()
        print(f"UDP receiver listening on 127.0.0.1:{UDP_PORT}")

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

        run_seconds = int(
            input(f"Run duration in seconds (default {DEFAULT_RUN_SECONDS}): ").strip()
            or DEFAULT_RUN_SECONDS
        )

        if use_stdin_keyboard:
            keyboard = SSHKeyboardTeleop()
            keyboard.connect()

        wait_for_first_udp_packet(receiver)

        metrics = MetricsLogger(LOGS_DIR / "after.csv")
        print(f"Logging to {metrics.csv_path}")

        try:
            p_control_loop(
                robot,
                keyboard,
                target_positions,
                start_positions,
                current_x,
                current_y,
                receiver,
                metrics,
                run_seconds=run_seconds,
            )
        finally:
            metrics.close()
            receiver.close()
            robot.disconnect()
            keyboard.disconnect()
            print("Program ended")

    except Exception as e:
        print(f"Program execution failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
