export const deck = {
  title: 'Teaching a Robot Arm to Grasp in Simulation',

  slides: {

    s1: {
      tag: 'AIPI 590 · Challenge 3 · Spring 2026',
      title: 'Teaching a Robot Arm to <em>Grasp in Simulation</em>',
      subtitle: 'SAC + Hindsight Experience Replay on FetchPickAndPlace',
      name: 'Lindsay Gross · Yifei Guo · Jonas Neves',
      speaker: 'Lindsay',
      notes: `**WHAT WE DID:** trained a simulated 7-DOF Fetch robot arm to pick up an object and place it at a target location using reinforcement learning. **CORE CHALLENGE:** sparse reward — the robot only gets signal when it succeeds, which almost never happens randomly. **OUR APPROACH:** SAC + HER, which converts failures into useful training data.`,
    },

    s2: {
      tag: 'THE PROBLEM',
      heading: 'Sparse Rewards Make <em>Manipulation</em> Nearly Impossible',
      bullets: [
        'FetchPickAndPlace: reach, grasp, lift, and place an object at a random 3D target',
        'Reward is binary: 0 if within 5 cm of goal, −1 otherwise — no gradient to follow',
        'Random policy success rate ≈ 0% — the robot never stumbles into a correct grasp',
      ],
      callout: 'Without goal relabeling, the agent trains on millions of −1 rewards and learns nothing.',
      speaker: 'Lindsay',
      notes: `**WHY IT'S HARD:** 4D continuous action space (3 arm + 1 gripper), sparse reward, random target position each episode. A random policy literally never succeeds. **THE INSIGHT:** we need a way to learn from failure.`,
    },

    s3: {
      tag: 'OUR APPROACH',
      heading: 'SAC + <em>Hindsight Experience Replay</em>',
      pipeline: [
        { label: 'SAC', desc: 'Off-policy, entropy-regularized' },
        { label: 'HER', desc: 'Relabel failures as successes' },
        { label: 'Eval', desc: 'Measure success rate over time' },
      ],
      bullets: [
        '<strong>SAC:</strong> off-policy actor-critic with entropy bonus — explores contact variations without collapsing',
        '<strong>HER:</strong> "what if the goal was where the object ended up?" — relabels ~75% of failed episodes as successes',
        '<strong>Future strategy:</strong> goals sampled from later in the same episode — empirically strongest (Andrychowicz 2017)',
      ],
      speaker: 'Lindsay',
      notes: `**WHY SAC:** off-policy = sample efficient for expensive MuJoCo steps. Entropy regularization prevents premature convergence to a single grasp strategy. **WHY HER:** the key insight. If the robot knocked the object somewhere, we relabel that somewhere as the goal. Now the trajectory is a success. This gives dense learning signal from sparse rewards. **FUTURE STRATEGY:** relabeling goals from states later in the same episode works best.`,
    },

    s4: {
      tag: 'TRAINING SETUP',
      heading: 'Two Tasks, <em>Two Scales</em>',
      comparisonTable: {
        headers: ['', 'FetchReach', 'FetchPickAndPlace'],
        rows: [
          ['Task', 'Move end-effector to target', 'Grasp + place object at target'],
          ['Timesteps', '200K', '1M'],
          ['Environments', '8 parallel', '8 parallel'],
          ['Network', '[256, 256, 256]', '[256, 256, 256]'],
          ['HER goals', '4 per transition', '4 per transition'],
          ['Training time', '~19 min (T4)', '~4.5 hrs (A100)'],
        ],
      },
      callout: 'FetchReach validates the pipeline on a simpler task before scaling to full manipulation.',
      speaker: 'Yifei',
      notes: `**WHY TWO TASKS:** Reach is the sanity check — if SAC+HER can't solve reaching, something is broken. PickAndPlace is the real challenge — gripper control, contact physics, lifting. **SHARED SETUP:** same network architecture, same HER config, same vectorized training. Only difference is timestep budget (200K vs 1M). **TRAINING TIME:** Reach took 19 minutes on a T4. PickAndPlace took 4.5 hours on an A100 — the 14x time difference comes from 5x more timesteps plus contact physics being more expensive to simulate. **WHY [256,256,256]:** standard for MuJoCo manipulation — enough capacity without overfitting on the goal-conditioned observation space.`,
    },

    s5: {
      tag: 'RESULTS · REACH',
      heading: 'FetchReach: <em>100% by 80K Steps</em>',
      stats: [
        { label: 'Budget', value: '200K' },
        { label: 'Solved at', value: '80K' },
        { label: 'Success rate', value: '100%' },
        { label: 'Train time', value: '~19 min' },
      ],
      img: 'img/reach_curves.png',
      imgAlt: 'FetchReach training curves — reward and success rate over 200K timesteps',
      bullets: [
        'Sharp jump from 5% to 100% between 40K and 80K — once the arm-to-target mapping clicks, it generalizes to all goals',
        'Confirms SAC+HER pipeline works before scaling to manipulation',
      ],
      speaker: 'Yifei',
      notes: `**THE CURVE:** jumps from 5% to 100% between 40K and 80K. Not gradual — Reach is simple enough that once the policy learns the basic mapping, it works for all goal positions. Stays at 100% through the remaining budget. **WHAT THIS PROVES:** the pipeline works. Now we can trust the same setup on the harder task.`,
    },

    s6: {
      tag: 'RESULTS · PICK AND PLACE',
      heading: 'FetchPickAndPlace: <em>100% by 960K Steps</em>',
      stats: [
        { label: 'Budget', value: '1M' },
        { label: 'Solved at', value: '960K' },
        { label: 'Success rate', value: '100%' },
        { label: 'Train time', value: '~4.5 hrs' },
      ],
      img: 'img/pickandplace_curves.png',
      imgAlt: 'FetchPickAndPlace training curves — reward and success rate over 1M timesteps',
      bullets: [
        'Success rate climbs from 0% to 100% — full pick-lift-place behavior learned',
        'Reward curve tracks success rate — no reward hacking, clean alignment',
        'HER was essential: without it, the agent would train on 1M negative rewards',
      ],
      speaker: 'Yifei',
      notes: `**THE KEY RESULT:** 0% to 100% success. The robot learned to reach, grasp, lift, and place. **WHY THIS MATTERS:** without HER, this would be nearly impossible at this scale — random exploration almost never produces a successful grasp. **REWARD CURVE:** tracks success rate closely, meaning the reward is measuring what we want.`,
    },

    s7: {
      tag: 'DEMO',
      heading: 'Trained Policy in <em>Action</em>',
      img: 'img/pickandplace_rollout.gif',
      imgAlt: 'Animated rollout of trained PickAndPlace policy — robot picks up object and places it at goal',
      bullets: [
        'Deterministic rollout from the trained policy — reach, grasp, lift, place',
        'Interactive 3D viewer at <strong>aipi590-ggn.github.io/aipi590-challenge-3</strong>',
      ],
      speaker: 'Jonas',
      notes: `**WHAT YOU'RE SEEING:** a deterministic rollout from the best checkpoint. The arm reaches toward the object, closes the gripper, lifts it, and places it at the red target. **THE VIEWER:** we built an interactive Three.js viewer that plays back the actual MuJoCo geom transforms — same data as the video, matched frame-for-frame.`,
    },

    s8: {
      tag: 'SIM-TO-REAL GAPS',
      heading: 'Five Gaps Between <em>Sim and Real</em>',
      bullets: [
        '<strong>Actuator fidelity:</strong> MuJoCo uses ideal velocity control — real motors have backlash, torque limits, thermal drift',
        '<strong>Contact modeling:</strong> MuJoCo\'s soft constraints miss real gripper compliance and micro-slip during grasp',
        '<strong>Observation noise:</strong> sim gives ground-truth state vectors — real sensors have encoder noise and camera latency',
        '<strong>Control latency:</strong> sim steps at 2ms — real ROS 2 loop runs at 10ms, a 5x gap that compounds over trajectories',
        '<strong>Zero calibration:</strong> 2° wrist error at 650mm reach = 22mm end-effector offset — nearly half the 50mm success threshold consumed by calibration alone',
      ],
      speaker: 'Jonas',
      notes: `**THE FRAMEWORK:** from Week 9 — action gap (actuators), next-state gap (contacts), observation gap (sensors), reward gap (success metric changes). **THE BIGGEST RISK:** contact modeling — everything works in sim because MuJoCo's gripper has perfect compliance. On a real arm, the grasp would fail 80% of the time without adaptation. **CALIBRATION:** a 2-degree error at the wrist, at 650mm reach, produces 22mm of end-effector error. Our success threshold is 50mm. That's already eating half the budget.`,
    },

    s9: {
      tag: 'SIM-TO-REAL MITIGATION',
      heading: 'Domain Randomization <em>Strategy</em>',
      comparisonTable: {
        headers: ['Parameter', 'Range', 'Rationale'],
        rows: [
          ['Action delay', '0–20 ms', 'ROS 2 control loop jitter'],
          ['Joint obs noise', 'σ = 0.01 rad', 'Encoder resolution'],
          ['Goal obs noise', 'σ = 3 mm', 'Depth camera uncertainty'],
          ['Link mass', '±10%', 'Manufacturing tolerance'],
          ['Joint friction', '0.5–2× nominal', 'Thermal and wear variation'],
        ],
      },
      bullets: [
        '<strong>Beyond DR:</strong> residual policy learning on real hardware to fix systematic biases',
        '<strong>Real-to-sim:</strong> estimate true actuator dynamics from hardware trajectories, retrain',
      ],
      speaker: 'Jonas',
      notes: `**WHY THESE RANGES:** each is grounded in the actual hardware spec (reBot-DevArm, Robostride/Damiao motors). Not arbitrary — measured or specced. **RESIDUAL POLICY:** deploy the sim-trained base policy, collect real trajectories, train a small correction network. Fixes calibration drift and contact model errors without retraining from scratch. **REAL-TO-SIM:** use real data to update the simulator, then retrain. Isaac Sim integration planned for this.`,
    },

    s10: {
      tag: 'CONCLUSIONS',
      heading: 'What We Built, What We Learned',
      bullets: [
        '<strong>SAC+HER solves sparse-reward manipulation</strong> — 0% to 100% success on FetchPickAndPlace in 1M steps',
        '<strong>HER is the critical ingredient</strong> — relabeling failures as successes provides the only learning signal',
        '<strong>Sim-to-real is the real challenge</strong> — contact modeling and calibration are the dominant failure modes',
        '<strong>Interactive visualization</strong> — Three.js viewer plays back real MuJoCo transforms, matched to video',
      ],
      speaker: 'Yifei',
      notes: `**SUMMARY:** SAC+HER works — we trained a pick-and-place policy from scratch in ~4.5 hours on a single GPU. HER is essential — without it, no signal. Sim-to-real is the next frontier — our analysis maps the specific gaps and mitigations. Thanks.`,
    },

    s11: {
      tag: 'THANK YOU',
      title: 'Questions?',
      name: 'Lindsay Gross · Yifei Guo · Jonas Neves',
      speaker: 'All',
      notes: `**WHY SAC OVER PPO:** off-policy = replay buffer = sample efficient. PPO is on-policy, would need ~10x more environment steps. **WHY NOT REWARD SHAPING:** HER gives us dense signal without hand-designing a reward function — reward shaping is brittle and task-specific. **WHY 100% SUCCESS IN SIM BUT NOT REAL:** sim has perfect actuation, perfect sensing, perfect contact. Each of those assumptions breaks on hardware. That's exactly the sim-to-real gap.`,
    },
  },
};
