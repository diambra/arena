from diambra.arena.arena_imitation_learning_gym import ImitationLearning
from diambra.arena.utils.gym_utils import show_wrap_obs
import os
import numpy as np

# Show files in folder
base_path = os.path.dirname(os.path.abspath(__file__))
recorded_trajectories_folder = os.path.join(base_path, "recordedTrajectories")
recorded_trajectories_files = [os.path.join(recorded_trajectories_folder, f)
                               for f in os.listdir(recorded_trajectories_folder)
                               if os.path.isfile(os.path.join(recorded_trajectories_folder, f))]
print(recorded_trajectories_files)

# Imitation learning settings
settings = {}

# List of recorded trajectories files
settings["traj_files_list"] = recorded_trajectories_files

# Number of parallel Imitation Learning environments that will be run
settings["total_cpus"] = 2

# Rank of the created environment
settings["rank"] = 0

env = ImitationLearning(**settings)

observation = env.reset()
env.render(mode="human")
show_wrap_obs(observation, env.n_actions_stack, env.char_names)

# Show trajectory summary
env.traj_summary()

while True:

    dummy_actions = 0
    observation, reward, done, info = env.step(dummy_actions)
    env.render(mode="human")
    show_wrap_obs(observation, env.n_actions_stack, env.char_names)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if np.any(env.exhausted):
        break

    if done:
        observation = env.reset()
        env.render(mode="human")
        show_wrap_obs(observation, env.n_actions_stack, env.char_names)

env.close()
