# Challenge 3: RL in the Physical World — Working Context

## Current Status

**Status**: Complete (training finished, videos generated, README with GIFs published)

**Project**: Trained robotic grasping/reaching policies with SAC+HER in MuJoCo (FetchPickAndPlace-v4 and FetchReach-v4), with analysis of sim2real transfer gaps against the reBot-DevArm platform.

**Repo**: https://github.com/jonasneves/aipi590-challenge-3

## Key Decisions Made

1. **Task**: FetchPickAndPlace-v4 (not just reaching) — actual manipulation task with gripper control required. More aligned with "grasping" requirement than FetchReach-v3.

2. **Algorithm**: SAC + HER (Hindsight Experience Replay)
   - SAC: off-policy, sample-efficient, entropy regularization
   - HER: relabels sparse-reward failures as successes toward achieved goal
   - Needed because FetchPickAndPlace has almost-never-positive reward signal early in training

3. **Simulation Budget**: 1M timesteps for main notebook (challenge3.ipynb), 200k for v1 (challenge3-v1.ipynb)
   - Expected runtime: ~25 min on A100, ~60 min on T4
   - Colab Pro users should select A100 runtime manually from Runtime menu

4. **Live Visualization**: 4-panel ECharts dashboard in `colab_utils.LiveChartCallback`
   - Top-left: Episode Reward (rolling 100-ep mean)
   - Top-right: Success Rate (with area fill)
   - Bottom-left: Actor Loss + Critic Loss (dual series)
   - Bottom-right: Entropy Coefficient
   - Stats bar above: timesteps, episodes, fps, success %, elapsed, updates
   - Updates every 2000 steps (was 500 to reduce browser load)
   - Downsamples to max 300 data points to prevent JS memory bloat

5. **Headless Rendering**: Uses Xvfb virtual display for evaluation videos
   - Prepended to eval cells in both notebooks
   - Fixes "X11: DISPLAY variable missing" error

## Architecture

### Notebooks
- `challenge3-pickandplace.ipynb` — main: 1M timesteps, FetchPickAndPlace-v4, full sim2real analysis
- `challenge3-reach-experimentation.ipynb` — experimentation: 200k timesteps, FetchReach-v4, includes live chart

### Scripts
- `scripts/colab_utils.py` — contains:
  - `prepare_notebook()` — clone repo, handle auth
  - `publish_artifacts()` — OAuth button + git push (no manual secret needed)
  - `save_notebook()` — snapshot running notebook via `_message.blocking_request("get_ipynb")`
  - `LiveChartCallback` — SB3 callback, 4-panel ECharts, clear_output + full redraw every 2k steps

### Data Flow (Training)
1. Install deps → clone repo → setup paths
2. Create train/eval envs (Monitor wrapped)
3. SAC with HerReplayBuffer (n_sampled_goal=4, strategy='future')
4. EvalCallback runs every 20k steps, saves best_model
5. LiveChartCallback renders dashboard every 2k steps
6. Training metrics pulled from `model.logger.name_to_value`

## Known Issues & Workarounds

### Issue: Browser fan noise during training
**Root cause**: Full ECharts redraw every 500 steps = ~2000 redraws over 1M steps
**Solution**:
- Increased `update_freq` default from 500 → 2000 (4× fewer redraws)
- Added `max_points=300` downsampling so JS arrays stay bounded
- Tunable: `LiveChartCallback(update_freq=5000, max_points=200)` for even lighter load

### Issue: Colab notebook visualization broken with eval_js
**Root cause**: eval_js runs in main frame, ECharts div lives in output iframe — no shared window
**Solution**:
- Switched from eval_js to `clear_output(wait=True)` + `display(HTML(...))`
- Data baked into HTML template at render time (no cross-frame JS calls)
- Fully reliable, works in all Colab contexts

### Issue: MuJoCo rendering fails ("gladLoadGL error", "DISPLAY missing")
**Root cause**: Colab is headless, no X11 display
**Solution**:
- Prepend eval cells with Xvfb virtual display:
  ```python
  import subprocess, os
  subprocess.Popen(['Xvfb', ':1', '-screen', '0', '1024x768x24'])
  os.environ['DISPLAY'] = ':1'
  ```
- Applied to both challenge3.ipynb and challenge3-v1.ipynb

## Sim2Real Analysis Structure

Five major gaps between MuJoCo training and reBot-DevArm hardware:

1. **Contact & Gripper Modeling** (dominant) — finger compliance, micro-slip, asymmetry
2. **Actuator Fidelity** — backlash, control loop latency (~10ms ROS 2), torque saturation
3. **Observation Noise** — encoder resolution, camera uncertainty & pipeline latency
4. **Zero Calibration Drift** — per-joint errors compound through kinematic chain (22mm error at 650mm reach from 2°)
5. **Domain Randomization Strategy** — table with 7 parameters: action delay, observation noise, mass variance, friction range, object friction, gripper position noise, latency simulation

Beyond DR: residual policy learning + real-to-sim adaptation (Isaac Sim integration planned Q2 2026)

## Completion Status (2026-04-04)

✅ **Training**: Both models trained successfully
   - FetchReach-v4 (200k steps) — videos + GIFs generated
   - FetchPickAndPlace-v4 (1M steps) — started in Colab, output frames/gifs available

✅ **Videos & GIFs**: Converted to GIFs for inline README playback
   - 5 episode rollouts per model
   - Grid layout support added (2-column default)
   - Plays in GitHub README without external embeds

✅ **README**: Published with rollout videos and grid layout
   - Latest commit: "add grid layout support to update_readme_with_gifs"
   - Links to GitHub Releases for downloadable models

✅ **Publish Pipeline**: Working artifacts pipeline via `colab_utils.py`
   - OAuth-based Git push (no manual token paste)
   - Auto-collects results/ directory
   - Handles notebook JSON normalization

## Next Steps / Future Extensions

1. **Domain Randomization**: Add actuator delay, observation noise, friction variance wrappers
   - Would improve sim2real robustness
   - Parameters documented in working.md (section "Sim2Real Analysis Structure")

2. **Real Hardware Testing**: Deploy best_model.zip to reBot-DevArm platform
   - Measure actual vs simulated success rates
   - Identify dominant failure modes

3. **Algorithm Comparison**: Evaluate PPO, TD3 on same tasks
   - Cross-validate sample efficiency vs SAC+HER
   - Generate comparative training curves

4. **Residual Learning**: Train correction policy on hardware failures
   - Leaves SAC policy frozen, adds small residual network
   - Faster adaptation than retraining from scratch

## Files to Know

- `.claude/working.md` — this file
- `notebooks/challenge3.ipynb` — main work
- `notebooks/challenge3-v1.ipynb` — FetchReach variant
- `scripts/colab_utils.py` — all the Colab automation & visualization
- `results/models/best_model.zip` — trained policy (created after first eval callback)
- `results/videos/` — recorded rollouts
- `results/plots/` — training curves (matplotlib, saved after cell-plot)
- `requirements.txt` — deps (mujoco, gymnasium-robotics, stable-baselines3, moviepy)

## Metadata

- **Created**: 2026-04-04
- **Last Updated**: 2026-04-04 (session 2)
- **Challenge Due**: 2026-03-31 (passed deadline, but core work complete)
- **Team**: Jonas (user) + Claude (co-author)

## Recent Commits (Session 2)

1. `3676eb9` — add grid layout support to update_readme_with_gifs (2-column default)
2. `f55a1c6` — remove unused embed_videos_in_readme functions
3. `521c096` — add training GIFs [skip ci]
4. `1899dc4` — fix missing re import in update_readme_with_gifs

All commits post-deadline; challenge core work complete. These are polish/documentation updates.
