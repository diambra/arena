import diambraArena

# Mandatory parameters
diambraEnvKwargs = {}
diambraEnvKwargs["gameId"]   = "doapp" # Game selection
diambraEnvKwargs["romsPath"] = "/home/apalmas/Applications/Diambra/diambraengine/roms/mame/" # Path to roms folder
envId = "TestEnv" # This ID must be unique for every instance of the environment

# Additional game options
diambraEnvKwargs["render"] = True # Renders the environment, deactivate for speedup
diambraEnvKwargs["lockFps"] = False # Locks to 60 FPS, deactivate for speedup
diambraEnvKwargs["sound"] = diambraEnvKwargs["lockFps"] and diambraEnvKwargs["render"] # Activate game sound
diambraEnvKwargs["mameDiambraStepRatio"] = 6 # Number of steps performed by the game for every environment step, bounds: [1, 6]

diambraEnvKwargs["headless"] = False # Allows to execute the environment in headless mode (for server-side executions)

diambraEnvKwargs["player"] = "P1" # Player side selection: P1 (left), P2 (right), Random (50% P1, 50% P2)

# Game-specific options (see documentation for details)
diambraEnvKwargs["difficulty"]  = 3 # Game difficulty level
diambraEnvKwargs["characters"]  = [["Random", "Random"], ["Random", "Random"]] # Character to be used
diambraEnvKwargs["charOutfits"] = [2, 2] # Character outfit

env = diambraArena.make(envId, diambraEnvKwargs)

# Environment reset
observation = env.reset()

# Run for one episode
while True:

    # Action random sampling
    actions = env.action_space.sample()

    # Environmet step
    observation, reward, done, info = env.step(actions)

    # Check for episode end
    if done:
        # Environment reset
        observation = env.reset()
        break

# Close the environment
env.close()
