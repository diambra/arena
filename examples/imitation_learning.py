import diambra.arena
import os
import numpy as np

# Show files in folder
base_path = os.path.dirname(os.path.abspath(__file__))
recorded_traj_folder = os.path.join(base_path, "recordedTrajectories")
recorded_traj_files = [os.path.join(recorded_traj_folder, f)
                       for f in os.listdir(recorded_traj_folder)
                       if os.path.isfile(os.path.join(recorded_traj_folder, f))]
print(recorded_traj_files)

# Imitation learning settings
settings = {}

# List of recorded trajectories files
settings["traj_files_list"] = recorded_traj_files

# Number of parallel Imitation Learning environments that will be run
settings["total_cpus"] = 2

# Rank of the created environment
settings["rank"] = 0

env = diambra.arena.ImitationLearning(**settings)

observation = env.reset()
env.render(mode="human")
env.show_obs(observation)

# Show trajectory summary
env.traj_summary()

while True:

    dummy_actions = 0
    observation, reward, done, info = env.step(dummy_actions)
    env.render(mode="human")
    env.show_obs(observation)
    print("Reward: {}".format(reward))
    print("Done: {}".format(done))
    print("Info: {}".format(info))

    if np.any(env.exhausted):
        break

    if done:
        observation = env.reset()
        env.render(mode="human")
        env.show_obs(observation)

env.close()
