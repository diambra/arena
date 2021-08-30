import diambraArena
from diambraArena.gymUtils import showWrapObs
import os

# Show files in folder
basePath = os.path.dirname(os.path.abspath(__file__))
recordedTrajectoriesFolder = os.path.join(basePath, "recordedTrajectories")
recordedTrajectoriesFiles = [os.path.join(recordedTrajectoriesFolder, f)
                             for f in os.listdir(recordedTrajectoriesFolder)
                             if os.path.isfile(os.path.join(recordedTrajectoriesFolder, f))]
print(recordedTrajectoriesFiles)

# Imitation learning options
diambraILKwargs = {}
diambraILKwargs["trajFilesList"] = recordedTrajectoriesFiles
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
