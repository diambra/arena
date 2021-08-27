import diambraArena

# Mandatory parameters
diambraEnvKwargs = {}
diambraEnvKwargs["gameId"]   = "doapp" # Game selection
diambraEnvKwargs["romsPath"] = "/home/apalmas/Applications/Diambra/diambraengine/roms/mame/" # Path to roms folder
envId = "TestEnv" # This ID must be unique for every instance of the environment

# Environment creation
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
