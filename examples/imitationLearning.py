import diambraArena
from diambraArena.gymUtils import show_wrap_obs
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
settings["trajFilesList"] = recorded_trajectories_files

# Number of parallel Imitation Learning environments that will be run
settings["totalCpus"] = 2

# Rank of the created environment
settings["rank"] = 0

env = diambraArena.imitationLearning(**settings)

observation = env.reset()
env.render(mode="human")
show_wrap_obs(observation, env.nActionsStack, env.charNames)

# Show trajectory summary
env.trajSummary()

while True:

    dummy_actions = 0
    observation, reward, done, info = env.step(dummy_actions)
    env.render(mode="human")
    show_wrap_obs(observation, env.nActionsStack, env.charNames)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if np.any(env.exhausted):
        break

    if done:
        observation = env.reset()
        env.render(mode="human")
        show_wrap_obs(observation, env.nActionsStack, env.charNames)

env.close()
