import diambraArena

# Mandatory parameters
diambraEnvKwargs = {}
diambraEnvKwargs["gameId"]   = "doapp" # Game selection
diambraEnvKwargs["romsPath"] = "/home/apalmas/Applications/Diambra/diambraengine/roms/mame/" # Path to roms folder
envId = "TestEnv" # This ID must be unique for every instance of the environment

env = diambraArena.make(envId, diambraEnvKwargs)

observation = env.reset()

while True:

    actions = env.action_space.sample()

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

env.close()
