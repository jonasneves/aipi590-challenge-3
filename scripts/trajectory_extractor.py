"""Extract trajectory data and record videos from the same rollouts."""

import json
import numpy as np
import mujoco
import gymnasium as gym
import gymnasium_robotics
from pathlib import Path


FETCH_MESH_GEOMS = [
    'robot0:base_link',
    'robot0:torso_lift_link',
    'robot0:shoulder_pan_link',
    'robot0:shoulder_lift_link',
    'robot0:upperarm_roll_link',
    'robot0:elbow_flex_link',
    'robot0:forearm_roll_link',
    'robot0:wrist_flex_link',
    'robot0:wrist_roll_link',
    'robot0:gripper_link',
]

FETCH_FINGER_GEOMS = [
    'robot0:r_gripper_finger_link',
    'robot0:l_gripper_finger_link',
]


def _get_geom_transforms(model, data):
    """Get world-frame position and quaternion for each visualization geom."""
    transforms = {}
    for geom_name in FETCH_MESH_GEOMS + FETCH_FINGER_GEOMS:
        try:
            gid = model.geom(geom_name).id
            pos = data.geom_xpos[gid].tolist()
            quat = np.zeros(4)
            mujoco.mju_mat2Quat(quat, data.geom_xmat[gid])
            transforms[geom_name] = {
                'pos': pos,
                'quat': quat.tolist(),
            }
        except Exception:
            pass
    return transforms


def _get_table_info(model, data):
    """Get table position from the MuJoCo model."""
    for name in ['table0', 'table']:
        try:
            bid = model.body(name).id
            return data.xpos[bid].tolist()
        except Exception:
            continue
    return None


def extract_trajectory(
    model,
    env_id: str = 'FetchPickAndPlace-v4',
    n_episodes: int = 1,
    deterministic: bool = True,
    video_dir: str | Path | None = None,
    video_prefix: str | None = None,
) -> list[dict]:
    """Run policy rollouts, extract trajectory data and optionally record videos.

    When video_dir is provided, videos are recorded from the same environment
    instance and episodes as the trajectory data, so they match exactly.
    """
    gym.register_envs(gymnasium_robotics)

    render_mode = 'rgb_array' if video_dir else None
    env = gym.make(env_id, render_mode=render_mode)

    if video_dir:
        video_dir = Path(video_dir)
        video_dir.mkdir(parents=True, exist_ok=True)
        if video_prefix is None:
            video_prefix = env_id.split('-')[0].lower()
        env = gym.wrappers.RecordVideo(
            env,
            str(video_dir),
            episode_trigger=lambda ep: True,
            name_prefix=video_prefix,
        )

    mj_model = env.unwrapped.model
    mj_data = env.unwrapped.data

    episodes = []
    successes = 0

    for ep in range(n_episodes):
        obs, _ = env.reset()

        trajectory = {
            'episode': ep,
            'task': env_id,
            'table_position': _get_table_info(mj_model, mj_data),
            'timesteps': [],
        }

        done = False
        step = 0

        while not done:
            action, _ = model.predict(obs, deterministic=deterministic)

            achieved = obs.get('achieved_goal', np.array([0, 0, 0]))
            desired = obs.get('desired_goal', np.array([0, 0, 0]))

            timestep = {
                'step': step,
                'geoms': _get_geom_transforms(mj_model, mj_data),
                'object_position': achieved[:3].tolist() if hasattr(achieved, 'tolist') else list(achieved[:3]),
                'goal_position': desired[:3].tolist() if hasattr(desired, 'tolist') else list(desired[:3]),
            }
            trajectory['timesteps'].append(timestep)

            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            step += 1

        success = bool(info.get('is_success', False))
        trajectory['success'] = success
        trajectory['length'] = step
        episodes.append(trajectory)
        if success:
            successes += 1

    env.close()
    print(f'Success rate: {successes}/{n_episodes}')
    return episodes


def save_trajectories(episodes, output_path):
    """Save trajectory data as JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def convert(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)): return float(obj) if isinstance(obj, np.floating) else int(obj)
        if isinstance(obj, np.bool_): return bool(obj)
        if isinstance(obj, dict): return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)): return [convert(i) for i in obj]
        return obj

    with open(output_path, 'w') as f:
        json.dump(convert(episodes), f)
    print(f'Saved {len(episodes)} trajectories to {output_path}')


def generate_versioned_filename(env_id, n_episodes):
    task_name = env_id.split('-')[0].lower()
    return f'trajectories-{task_name}-{n_episodes}ep.json'
