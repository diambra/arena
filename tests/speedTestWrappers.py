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
        parser.add_argument('--stepRatio',  type=int, default=1,          help='Frame ratio')
        parser.add_argument('--nEpisodes',   type=int, default=1,          help='Number of episodes')
        parser.add_argument('--actionSpace', type=str, default="discrete", help='(discrete)/multidiscrete')
        parser.add_argument('--attButComb',  type=int, default=0,          help='If to use attack button combinations (0=False)/1=True')
        parser.add_argument('--targetSpeed', type=int, default=100,        help='Reference speed')
        parser.add_argument('--libPath',     type=str, default="",         help='Path to diambraEnvLib')
        opt = parser.parse_args()
        print(opt)

        # Settings
        settings = {}
        settings["romsPath"] = opt.romsPath
        if opt.libPath != "":
            settings["libPath"]  = opt.libPath

        settings["gameId"]     = opt.gameId
        settings["player"]     = opt.player

        settings["stepRatio"] = opt.stepRatio
        settings["render"] = False
        settings["lockFps"] = False

        settings["continueGame"] = 0.0
        settings["showFinal"]    = False

        settings["actionSpace"] = [opt.actionSpace, opt.actionSpace]
        settings["attackButCombination"] = [opt.attButComb, opt.attButComb]
        if settings["player"] != "P1P2":
            settings["actionSpace"] = settings["actionSpace"][0]
            settings["attackButCombination"] = settings["attackButCombination"][0]

        # Recording settings
        trajRecSettings = None

        # Env wrappers settings
        wrappersSettings = {}
        wrappersSettings["noOpMax"] = 0
        wrappersSettings["stickyActions"] = 1
        wrappersSettings["hwcObsResize"] = [128, 128, 1]
        wrappersSettings["normalizeRewards"] = True
        wrappersSettings["clipRewards"] = False
        wrappersSettings["frameStack"] = 4
        wrappersSettings["dilation"] = 1
        wrappersSettings["actionsStack"] = 12
        wrappersSettings["scale"] = True
        wrappersSettings["scaleMod"] = 0

        envId = opt.gameId + "_speedTestWrappers"
        env = diambraArena.make(envId, settings, wrappersSettings, trajRecSettings, seed=timeDepSeed)

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
            if settings["player"] != "P1P2":
                actions = env.action_space.sample()

            else:
                for idx in range(2):
                    actions[idx] = env.action_space["P{}".format(idx+1)].sample()

            if settings["player"] == "P1P2" or settings["actionSpace"] != "discrete":
                actions = np.append(actions[0], actions[1])

            observation, reward, done, info = env.step(actions)

            if done:
                currNumEp += 1
                print("Ep. # = ", currNumEp)

                observation = env.reset()

        env.close()

        fpsVal2 = reject_outliers(fpsVal)
        avgFps = np.mean(fpsVal2)
        print("Average speed = {} FPS, STD {} FPS".format(avgFps, np.std(fpsVal2)))

        if abs(avgFps - opt.targetSpeed) > opt.targetSpeed*0.025:
            raise RuntimeError("Fps different than expected: {} VS {}".format(avgFps, opt.targetSpeed))

        print("ALL GOOD!")
    except Exception as e:
        print(e)
        print("ALL BAD")
