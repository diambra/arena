from diambraGym import diambraGym
import os

base_path = "/home/path-to-repo-root/" # Edit accordingly

diambraEnvKwargs = {}
diambraEnvKwargs["gameId"]          = "doapp" # Game selection
diambraEnvKwargs["diambraEnv_path"] = os.path.join(base_path, "diambraEnvLib/")
diambraEnvKwargs["roms_path"]       = os.path.join(base_path, "roms/") # Absolute path to roms
diambraEnvKwargs["mame_path"]       = os.path.join(base_path, "mame/") # Absolute path to MAME executable

diambraEnvKwargs["mame_diambra_step_ratio"] = 6
diambraEnvKwargs["render"]                  = True # Renders the environment, deactivate for speedup
diambraEnvKwargs["lock_fps"]                = True # Locks to 60 FPS
diambraEnvKwargs["sound"]                   = diambraEnvKwargs["lock_fps"] and diambraEnvKwargs["render"]

# 1P
diambraEnvKwargs["player"] = "P1"

# Game specific
diambraEnvKwargs["difficulty"]  = 3
diambraEnvKwargs["characters"]  = [["Random", "Random"], ["Random", "Random"]]
diambraEnvKwargs["charOutfits"] = [2, 2]

env = diambraGym("Test", diambraEnvKwargs, headless=False) # Use `headless=True` for server-side executions

observation = env.reset()

for _ in range(100):

    actions = env.action_spaces[0].sample() # Sampling for 1P mode

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()

env.close()
