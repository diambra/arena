import diambraArena
from diambraArena.gymUtils import showWrapObs
from os import listdir

# Show files in folder
trajRecFolder = opt.path
trajectoriesFiles = [os.path.join(trajRecFolder, f) for f in listdir(trajRecFolder) if os.path.isfile(os.path.join(trajRecFolder, f))]
print(trajectoriesFiles)

# Imitation learning options
diambraILKwargs = {}
diambraILKwargs["trajFilesList"] = trajectoriesFiles
diambraILKwargs["totalCpus"] = 2

env = diambraArena.imitationLearning(**diambraILKwargs)

observation = env.reset()
env.trajSummary()
env.render(mode="human")
showWrapObs(observation, env.nActionsStack, env.charNames)

while currNumEp < maxNumEp:

    dummyActions = 0
    observation, reward, done, info = env.step(dummyActions)
    env.render(mode="human")
    showWrapObs(observation, env.nActionsStack, env.charNames)

    if np.any(env.exhausted):
        break

    if done:
        observation = env.reset()
        env.render(mode="human")
        showWrapObs(observation, env.nActionsStack, env.charNames)

env.close()
