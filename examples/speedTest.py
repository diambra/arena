import diambraArena
import argparse, time
import numpy as np

def reject_outliers(data):
    m = 2
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered

parser = argparse.ArgumentParser()
parser.add_argument('--romsPath', type=str, required=False, help='Absolute path to roms')
opt = parser.parse_args()
print(opt)

# Mandatory parameters
settings = {}
settings["gameId"]   = "doapp"
if opt.romsPath is not None:
    settings["romsPath"] = opt.romsPath

settings["stepRatio"] = 1
settings["lockFps"] = False
settings["render"] = False

env = diambraArena.make("TestEnv", settings)

observation = env.reset()

tic = time.time()
fpsVal = []

while True:

    toc = time.time()
    fps = 1/(toc - tic)
    tic = toc
    fpsVal.append(fps)

    actions = [0, 0]

    observation, reward, done, info = env.step(actions)

    if done:
        observation = env.reset()
        break

env.close()

fpsVal2 = reject_outliers(fpsVal)
avgFps = np.mean(fpsVal2)
print("Average speed = {} FPS, STD {} FPS".format(avgFps, np.std(fpsVal2)))
