from diambra_environment.diambraGym import diambraGym
import os

repo_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../") # Absolute path to your DIAMBRA environment repo

diambraEnvKwargs = {}
diambraEnvKwargs["gameId"]          = "doapp" # Game selection
diambraEnvKwargs["roms_path"]       = os.path.join(repo_base_path, "roms/") # Absolute path to roms

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

envId = "AIAgent" # This ID must be unique for every instance of the environment when using diambraGym class
env = diambraGym(envId, diambraEnvKwargs, headless=False) # Use `headless=True` for server-side executions

observation = env.reset()

for _ in range(100):

    actions = env.action_spaces[0].sample() # Sampling for 1P mode

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()

env.close()
