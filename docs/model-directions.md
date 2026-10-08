# How this task relates to imitation learning, VLA and world models

The current project is human-video tracking plus hand-coded geometric retargeting in simulation. No policy or world model has been trained. The human footage supplies recorded planar movement; simulation supplies robot observations and controller action labels.

## Imitation policy

A compact behaviour-cloning policy can learn next-action predictions from validated simulation replay observation/action pairs. Initial inputs can be robot, cube and target relative state, with planar Cartesian actions as outputs. It then needs closed-loop testing, including recovery from deviations. A low prediction error alone is insufficient.

## VLA extension

A vision-language-action policy takes visual input and language instructions and produces robot actions. See the primary [OpenVLA paper](https://proceedings.mlr.press/v270/kim25c.html). Our overhead video is currently converted into coordinates offline; the controller does not consume camera images or language, so this implementation is not a VLA. A future VLA branch could use simulated images and goal instructions, but collecting diverse goals and verifying that instructions affect behavior would make that extension more meaningful than adding a constant text label to this single task.

## World-model extension

A learned dynamics model predicts what happens after an action. In this task a small state-based model could predict the next cube position (and possibly rotation) from current cube/robot state and a pushing action. Evaluate one-step and multi-step predictions on held-out episodes, including contact failures, then optionally use it for planning. A simple state-based predictor does not need image generation. See [Dreamer](https://arxiv.org/abs/1912.01603) for a richer model that learns latent dynamics and behaviors through imagined trajectories.

MuJoCo supplies known simulated physics; running MuJoCo or transforming a path is not training a learned world model. A model trained on simulation rollouts should be reported as learning simulation dynamics, not as having recovered real table friction from the human videos.

## Practical order

Finish and inspect the geometric baseline, train/evaluate the small imitation policy, and collect more personally recorded demonstrations if failures reveal missing coverage. With the extended deadline, a compact learned dynamics model is a natural additional experiment. The challenge summary supplied by the user permits hand-coded approaches; using a VLA or world model is optional, and the PDF has not been independently checked.
