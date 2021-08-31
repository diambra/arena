import diambraArena
import argparse, time
import numpy as np

def reject_outliers(data):
    m = 2
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if (u - 2 * s < e < u + 2 * s)]
    return filtered

if __name__ == '__main__':
    timeDepSeed = int((time.time()-int(time.time()-0.5))*1000)

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--romsPath',    type=str, required=True,      help='Absolute path to roms')
        parser.add_argument('--gameId',      type=str, default="doapp",    help='Game ID [(doapp), sfiii3n, tektagt, umk3]')
        parser.add_argument('--player',      type=str, default="Random",   help='Player [(Random), P1, P2, P1P2]')
        parser.add_argument('--frameRatio',  type=int, default=1,          help='Frame ratio')
        parser.add_argument('--nEpisodes',   type=int, default=1,          help='Number of episodes')
        parser.add_argument('--actionSpace', type=str, default="discrete", help='(discrete)/multidiscrete')
        parser.add_argument('--attButComb',  type=int, default=0,          help='If to use attack button combinations (0=False)/1=True')
        parser.add_argument('--targetSpeed', type=int, default=100,        help='Reference speed')
        parser.add_argument('--libPath',     type=str, default="",         help='Path to diambraEnvLib')
        opt = parser.parse_args()
        print(opt)

        # Common settings
        diambraKwargs = {}
        diambraKwargs["romsPath"] = opt.romsPath
        if opt.libPath != "":
            diambraKwargs["libPath"]  = opt.libPath

        diambraKwargs["gameId"]     = opt.gameId
        diambraKwargs["player"]     = opt.player
        diambraKwargs["characters"] = [["Random", "Random"], ["Random", "Random"]]

        diambraKwargs["mameDiambraStepRatio"] = opt.frameRatio
        diambraKwargs["render"] = False
        diambraKwargs["lockFps"] = False

        diambraKwargs["continueGame"] = 0.0
        diambraKwargs["showFinal"]    = False

        diambraKwargs["charOutfits"] = [2, 2]

        # DIAMBRA gym kwargs
        diambraGymKwargs = {}
        diambraGymKwargs["actionSpace"] = [opt.actionSpace, opt.actionSpace]
        diambraGymKwargs["attackButCombinations"] = [opt.attButComb, opt.attButComb]
        if diambraKwargs["player"] != "P1P2":
            diambraGymKwargs["actionSpace"] = diambraGymKwargs["actionSpace"][0]
            diambraGymKwargs["attackButCombinations"] = diambraGymKwargs["attackButCombinations"][0]

        envId = opt.gameId + "_speedTestGym"
        env = diambraArena.make(envId, diambraKwargs, diambraGymKwargs, seed=timeDepSeed)

        observation = env.reset()

        maxNumEp = opt.nEpisodes
        currNumEp = 0

        tic = time.time()
        fpsVal = []

        while currNumEp < maxNumEp:

            toc = time.time()
            fps = 1/(toc - tic)
            tic = toc
            #print("FPS = {}".format(fps))
            fpsVal.append(fps)

            actions = [None, None]
            if diambraKwargs["player"] != "P1P2":
                actions = env.action_space.sample()
            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx+1)].sample()

            if diambraKwargs["player"] == "P1P2" or diambraGymKwargs["actionSpace"] != "discrete":
                actions = np.append(actions[0], actions[1])

            observation, reward, done, info = env.step(actions)

            if done:
                print("Resetting Env")
                currNumEp += 1
                observation = env.reset()

        env.close()

        fpsVal2 = reject_outliers(fpsVal)
        avgFps = np.mean(fpsVal2)
        print("Average speed = {} FPS, STD {} FPS", avgFps, np.std(fpsVal2))

        if abs(avgFps - opt.targetSpeed) > opt.targetSpeed*0.025:
            raise RuntimeError("Fps different than expected: {} VS {}".format(avgFps, opt.targetSpeed))

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
