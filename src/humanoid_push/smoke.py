"""Checkpoint 1: scripted Cartesian Panda motion and headless video.

No human data is used here. This checks installation, control, and rendering only.
"""
import argparse
import json
import os
from pathlib import Path
import time

# Must be set before importing MuJoCo / robosuite.
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", os.environ["MUJOCO_GL"])
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path.cwd() / ".cache" / "numba"))

import imageio.v2 as imageio
import numpy as np
import robosuite as suite
from robosuite.controllers import load_composite_controller_config
from scipy.spatial.transform import Rotation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/smoke"))
    parser.add_argument("--camera", default="frontview")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--steps", type=int, default=180)
    args = parser.parse_args()
    if args.steps < 100:
        parser.error("--steps must be at least 100 to complete the motion check")
    args.output.mkdir(parents=True, exist_ok=True)
    np.random.seed(args.seed)
    config = load_composite_controller_config(robot="Panda")
    config["body_parts"]["right"]["input_ref_frame"] = "world"
    env = suite.make(
        "Lift", robots="Panda", controller_configs=config,
        initialization_noise=None, has_renderer=False,
        has_offscreen_renderer=True, use_camera_obs=False,
        control_freq=20, horizon=args.steps, ignore_done=True,
        hard_reset=False,
    )
    started = time.monotonic()
    positions, targets, actions = [], [], []
    video = args.output / "panda_motion.mp4"
    try:
        obs = env.reset()
        origin = obs["robot0_eef_pos"].copy()
        orientation = Rotation.from_quat(obs["robot0_eef_quat"])
        # A 10 cm excursion and return, with fixed initial orientation.
        # Delta position commands are normalised: action 1 maps to 0.05 m.
        with imageio.get_writer(video, fps=20, codec="libx264", quality=8,
                                macro_block_size=16) as writer:
            for step in range(args.steps):
                phase = step / (args.steps - 1)
                offset = 0.10 * np.sin(np.pi * phase) ** 2
                target = origin + np.array([0.0, offset, 0.0])
                action = np.zeros(env.action_dim)
                action[:3] = np.clip((target - obs["robot0_eef_pos"]) / 0.05, -0.25, 0.25)
                rotation_error = (orientation * Rotation.from_quat(obs["robot0_eef_quat"]).inv()).as_rotvec()
                action[3:6] = np.clip(rotation_error / 0.5, -0.25, 0.25)
                action[-1] = 1.0  # closed gripper
                obs, _, _, _ = env.step(action)
                positions.append(obs["robot0_eef_pos"].copy())
                targets.append(target)
                actions.append(action.copy())
                frame = env.sim.render(width=640, height=480, camera_name=args.camera)
                # MuJoCo's offscreen buffer is bottom-up.
                writer.append_data(np.ascontiguousarray(frame[::-1]))
                if (step + 1) % 60 == 0:
                    print(f"Rendered {step + 1}/{args.steps} frames", flush=True)
        positions = np.asarray(positions)
        targets = np.asarray(targets)
        movement = float(np.max(np.linalg.norm(positions - origin, axis=1)))
        rmse = float(np.sqrt(np.mean(np.sum((positions - targets) ** 2, axis=1))))
        finite = bool(np.isfinite(positions).all() and np.isfinite(env.sim.data.qpos).all())
        # Decode the saved file: a nonempty file alone is not sufficient.
        reader = imageio.get_reader(video)
        try:
            decoded_frames = sum(1 for _ in reader)
        finally:
            reader.close()
        passed = finite and movement > 0.07 and rmse < 0.025 and decoded_frames == args.steps
        result = {
            "checkpoint": "scripted Panda motion; no human data; no push evaluation",
            "passed": passed, "seed": args.seed, "steps": args.steps,
            "control_hz": 20, "robosuite": suite.__version__,
            "mujoco_gl": os.environ["MUJOCO_GL"], "camera": args.camera,
            "max_eef_displacement_m": movement, "tracking_rmse_m": rmse,
            "finite_state": finite, "decoded_frames": decoded_frames,
            "wall_seconds": time.monotonic() - started,
            "video": str(video),
        }
        np.savez_compressed(args.output / "trajectory.npz", eef_xyz=positions,
                            target_xyz=targets, actions=np.asarray(actions))
        (args.output / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
        reader = imageio.get_reader(video)
        try:
            imageio.imwrite(args.output / "preview.png", reader.get_data(args.steps // 2))
        finally:
            reader.close()
        print(json.dumps(result, indent=2), flush=True)
        if not passed:
            raise SystemExit("Smoke test failed; inspect metrics.json and video")
    finally:
        env.close()


if __name__ == "__main__":
    main()
