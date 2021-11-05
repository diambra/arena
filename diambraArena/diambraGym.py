import sys, platform, os
import numpy as np
import gym
from gym import spaces
from collections import deque
from diambraArena.gymUtils import discreteToMultiDiscreteAction
from diambraArena.diambraEnvLib.libInterface import diambraArenaLib

# DIAMBRA Env Gym
class diambraGymHardCoreBase(gym.Env):
    """Diambra Environment gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, envId, envSettings, rewNormFac, actionSpace, attackButCombination):
        super(diambraGymHardCoreBase, self).__init__()

        self.rewNormFac = rewNormFac
        self.actionSpace = actionSpace
        self.attackButCombination=attackButCombination

        print("EnvId = {}".format(envId))
        print("Action Spaces = {}".format(self.actionSpace))
        print("Use attack buttons combinations = {}".format(self.attackButCombination))

        # Launch DIAMBRA Arena
        self.diambraArena = diambraArenaLib(envId, envSettings)
        self.envSettings = self.diambraArena.envSettings

        # Get Env Info
        envInfo = self.diambraArena.readEnvInfo()
        self.envInfoProcess(envInfo)
        self.playerSide = self.envSettings["player"]

        # Read Env Int Data List
        self.diambraArena.readEnvIntDataVarsList()

        # Image as input:
        self.observation_space = spaces.Box(low=0, high=255,
                                        shape=(self.hwcDim[0], self.hwcDim[1], self.hwcDim[2]), dtype=np.uint8)

    # Processing Environment info
    def envInfoProcess(self, envInfo):
        # N actions
        self.nActionsButComb   = [int(envInfo[0]), int(envInfo[1])]
        self.nActionsNoButComb = [int(envInfo[2]), int(envInfo[3])]
        # N actions
        self.nActions = [self.nActionsButComb, self.nActionsButComb]
        for idx in range(2):
            if not self.attackButCombination[idx]:
                self.nActions[idx] = self.nActionsNoButComb

        # Frame height, width and channel dimensions
        self.hwcDim = [int(envInfo[4]), int(envInfo[5]), int(envInfo[6])]
        self.diambraArena.setFrameSize(self.hwcDim)

        # Maximum difference in players health
        self.maxDeltaHealth = int(envInfo[7]) - int(envInfo[8])

        # Maximum number of stages (1P game vs COM)
        self.maxStage = int(envInfo[9])

        # Game difficulty
        self.difficulty = int(envInfo[10])

        # Number of characters of the game
        self.numberOfCharacters = int(envInfo[11])

        # Characters names list
        currentIdx = 12
        self.charNames = []
        for idx in range(currentIdx, currentIdx + self.numberOfCharacters):
            self.charNames.append(envInfo[idx])

        currentIdx = currentIdx + self.numberOfCharacters

        # Action list
        moveList = ()
        for idx in range(currentIdx, currentIdx + self.nActionsButComb[0]):
            moveList += (envInfo[idx],)

        currentIdx += self.nActionsButComb[0]

        attackList = ()
        for idx in range(currentIdx, currentIdx + self.nActionsButComb[1]):
            attackList += (envInfo[idx],)

        currentIdx += self.nActionsButComb[1]

        self.actionList = (moveList, attackList)

        # Action dict
        moveDict = {}
        for idx in range(currentIdx, currentIdx + 2*self.nActionsButComb[0], 2):
            moveDict[int(envInfo[idx])] = envInfo[idx+1]

        currentIdx += 2*self.nActionsButComb[0]

        attackDict = {}
        for idx in range(currentIdx, currentIdx + 2*self.nActionsButComb[1], 2):
            attackDict[int(envInfo[idx])] = envInfo[idx+1]

        self.printActionsDict = [moveDict, attackDict]

        currentIdx += 2*self.nActionsButComb[1]

        # Additional Obs map
        numberOfAddObs = int(envInfo[currentIdx])
        currentIdx += 1
        self.addObs = {}
        for idx in range(numberOfAddObs):
            self.addObs[envInfo[currentIdx]] = [int(envInfo[currentIdx+1]),
                                                int(envInfo[currentIdx+2]),
                                                int(envInfo[currentIdx+3])]
            currentIdx += 4

    # Return env action list
    def actionList(self):
        return self.actionList

    # Print Actions
    def printActions(self):
        print("Move actions:")
        for k, v in self.printActionsDict[0].items():
            print(" {}: {}".format(k,v))

        print("Attack actions:")
        for k, v in self.printActionsDict[1].items():
            print(" {}: {}".format(k,v))

    # Step method to be implemented in derived classes
    def step(self, action):
        raise NotImplementedError()

    # Resetting the environment
    def resetComplete(self):
        self.diambraArena.reset()
        # Read specific info after resett
        resetInfo = self.diambraArena.readResetInfo()
        self.playerSide = resetInfo[0]
        self.savedFramesNum = int(resetInfo[1])
        observation, data = self.diambraArena.readData()

        return observation, data

    # Resetting the environment
    def reset(self):
        observation, data = self.resetComplete()

        return observation

    # Rendering the environment
    def render(self, mode='human'):
        pass

    # Closing the environment
    def close(self):
        # Close DIAMBRA Arena
        self.diambraArena.close()

# DIAMBRA Gym base class for single player mode
class diambraGymHardCore1P(diambraGymHardCoreBase):
    def __init__(self, envId, envSettings, rewNormFac=0.5,
                 actionSpace="multiDiscrete", attackButCombination=True):
        super().__init__( envId, envSettings, rewNormFac, actionSpace,
                          [attackButCombination, attackButCombination])

        # Define action and observation space
        # They must be gym.spaces objects

        if self.actionSpace == "multiDiscrete":
            # MultiDiscrete actions:
            # - Arrows -> One discrete set
            # - Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.MultiDiscrete(self.nActions[0])
            print("Using MultiDiscrete action space")
        elif self.actionSpace == "discrete":
            # Discrete actions:
            # - Arrows U Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.Discrete(self.nActions[0][0] + self.nActions[0][1] - 1)
            print("Using Discrete action space")
        else:
            raise Exception("Not recognized action space: {}".format(self.actionSpace))

    # Return min max rewards for the environment
    def minMaxRew(self):
        coeff = 1.0/self.rewNormFac
        return (-coeff*(self.maxStage-1)-2*coeff, self.maxStage*2*coeff)

    # Step the environment
    def stepComplete(self, action):
        # Actions initialization
        movAct = 0
        attAct = 0

        # Defining move and attack actions P1/P2 as a function of actionSpace
        if self.actionSpace == "multiDiscrete":
            movAct = action[0]
            attAct = action[1]
        else:
            # Discrete to multidiscrete conversion
            movAct, attAct = discreteToMultiDiscreteAction(action, self.nActions[0][0])

        self.diambraArena.step(movAct, attAct)
        self.savedFramesNum = self.diambraArena.readFlag()
        observation, data = self.diambraArena.readData()
        reward            = data["reward"]
        done              = data["epDone"]

        return observation, reward, done, data

    # Step the environment
    def step(self, action):

        observation, reward, done, data = self.stepComplete(action)

        return observation, reward, done,\
               {"roundDone": data["roundDone"], "stageDone": data["stageDone"],\
                "gameDone": data["gameDone"], "epDone": data["epDone"]}

# DIAMBRA Gym base class for two players mode
class diambraGymHardCore2P(diambraGymHardCoreBase):
    def __init__(self, envId, envSettings, rewNormFac=0.5,
                 actionSpace=["multiDiscrete", "multiDiscrete"],
                 attackButCombination=[True, True]):
        super().__init__( envId, envSettings, rewNormFac,
                          actionSpace, attackButCombination)

        # Define action spaces, they must be gym.spaces objects
        actionSpaceDict = {}
        for idx in range(2):
            if actionSpace[idx] == "multiDiscrete":
                actionSpaceDict["P{}".format(idx+1)] =\
                    spaces.MultiDiscrete(self.nActions[idx])
            else:
                actionSpaceDict["P{}".format(idx+1)] =\
                    spaces.Discrete(self.nActions[idx][0] + self.nActions[idx][1] - 1)

        self.action_space = spaces.Dict(actionSpaceDict)

    # Return min max rewards for the environment
    def minMaxRew(self):
        coeff = 1.0/self.rewNormFac
        return (-2*coeff, 2*coeff)

    # Step the environment
    def stepComplete(self, action):
        # Actions initialization
        movActP1 = 0
        attActP1 = 0
        movActP2 = 0
        attActP2 = 0

        # Defining move and attack actions P1/P2 as a function of actionSpace
        if self.actionSpace[0] == "multiDiscrete": # P1 MultiDiscrete Action Space
            # P1
            movActP1 = action[0]
            attActP1 = action[1]
            # P2
            if self.actionSpace[1] == "multiDiscrete": # P2 MultiDiscrete Action Space
                movActP2 = action[2]
                attActP2 = action[3]
            else: # P2 Discrete Action Space
                movActP2, attActP2 = discreteToMultiDiscreteAction(action[2], self.nActions[1][0])

        else: # P1 Discrete Action Space
            # P2
            if self.actionSpace[1] == "multiDiscrete": # P2 MultiDiscrete Action Space
                # P1
                # Discrete to multidiscrete conversion
                movActP1, attActP1 = discreteToMultiDiscreteAction(action[0], self.nActions[0][0])
                movActP2 = action[1]
                attActP2 = action[2]
            else: # P2 Discrete Action Space
                # P1
                # Discrete to multidiscrete conversion
                movActP1, attActP1 = discreteToMultiDiscreteAction(action[0], self.nActions[0][0])
                movActP2, attActP2 = discreteToMultiDiscreteAction(action[1], self.nActions[1][0])

        self.diambraArena.step(movActP1, attActP1, movActP2, attActP2)
        self.savedFramesNum = self.diambraArena.readFlag()
        observation, data = self.diambraArena.readData()
        reward            = data["reward"]
        done              = data["gameDone"]
        #data["epDone"]   = done

        return observation, reward, done, data

    # Step the environment
    def step(self, action):

        observation, reward, done, data = self.stepComplete(action)

        return observation, reward, done,\
               {"roundDone": data["roundDone"], "stageDone": data["stageDone"],\
                "gameDone": data["gameDone"], "epDone": data["epDone"]}

# DIAMBRA Gym base class providing frame and additional info as observations
class diambraGym1P(diambraGymHardCore1P):
    def __init__(self, envId, envSettings, rewNormFac=0.5, actionSpace="multiDiscrete",
                 attackButCombination=True):
        super().__init__( envId, envSettings, rewNormFac, actionSpace, attackButCombination)

        # Dictionary observation space
        observationSpaceDict = {}
        observationSpaceDict['frame'] = spaces.Box(low=0, high=255,
                                           shape=(self.hwcDim[0], self.hwcDim[1], self.hwcDim[2]), dtype=np.uint8)
        playerSpecDict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.addObs.items():

            if k == "stage":
                continue

            if k[-2:] == "P1":
                knew = "own"+k[:-2]
            else:
                knew = "opp"+k[:-2]

            if v[0] == 0 or v[0] == 2: # Discrete spaces (binary / categorical)
                playerSpecDict[knew] = spaces.Discrete(v[2]+1)
            elif v[0] == 1: # Box spaces
                playerSpecDict[knew] = spaces.Box(low=v[1], high=v[2],
                                                  shape=(), dtype=np.int32)

            else:
                raise RuntimeError("Only Discrete (Binary/Categorical) and Box Spaces allowed")

        actionsDict = {
            "move": spaces.Discrete(self.nActions[0][0]),
            "attack": spaces.Discrete(self.nActions[0][1])
        }

        playerSpecDict["actions"] = spaces.Dict(actionsDict)
        observationSpaceDict["P1"] = spaces.Dict(playerSpecDict)
        observationSpaceDict["stage"] = spaces.Box(low=self.addObs["stage"][1],
                                                   high=self.addObs["stage"][2],
                                                   shape=(), dtype=np.int8)

        self.observation_space = spaces.Dict(observationSpaceDict)

    def addObsIntegration(self, frame, data):

        observation = {}
        observation["frame"] = frame
        observation["stage"] = data["stage"]

        playerSpecDict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.addObs.items():

            if k == "stage":
                continue

            if k[-2:] == self.playerSide:
                knew = "own"+k[:-2]
            else:
                knew = "opp"+k[:-2]

            playerSpecDict[knew] = data[k]

        actionsDict = {
            "move": data["moveActionP1"],
            "attack": data["attackActionP1"],
        }

        playerSpecDict["actions"] = actionsDict
        observation["P1"] = playerSpecDict

        return observation

    def step(self, action):

        frame, reward, done, data = self.stepComplete(action)

        observation = self.addObsIntegration(frame, data)

        return observation, reward, done,\
               {"roundDone": data["roundDone"], "stageDone": data["stageDone"],\
                "gameDone": data["gameDone"], "epDone": data["epDone"]}

    # Reset the environment
    def reset(self, **kwargs):

        frame, data = self.resetComplete(**kwargs)

        observation = self.addObsIntegration(frame, data)

        return observation

# DIAMBRA Gym base class providing frame and additional info as observations
class diambraGym2P(diambraGymHardCore2P):
    def __init__(self, envId, envSettings, rewNormFac=0.5,
                 actionSpace=["multiDiscrete", "multiDiscrete"],
                 attackButCombination=[True, True]):
        super().__init__( envId, envSettings, rewNormFac, actionSpace,
                          attackButCombination)

        # Dictionary observation space
        observationSpaceDict = {}
        observationSpaceDict['frame'] = spaces.Box(low=0, high=255,
                                           shape=(self.hwcDim[0], self.hwcDim[1], self.hwcDim[2]), dtype=np.uint8)
        playerSpecDict = {}

        # Adding env additional observations (side-specific)
        for k, v in self.addObs.items():

            if k == "stage":
                continue

            if k[-2:] == "P1":
                knew = "own"+k[:-2]
            else:
                knew = "opp"+k[:-2]

            if v[0] == 0 or v[0] == 2: # Discrete spaces
                playerSpecDict[knew] = spaces.Discrete(v[2]+1)
            elif v[0] == 1: # Box spaces
                playerSpecDict[knew] = spaces.Box(low=v[1], high=v[2],
                                                  shape=(), dtype=np.int32)

            else:
                raise RuntimeError("Only Discrete and Box Spaces allowed")

        actionsDict = {
            "move": spaces.Discrete(self.nActions[0][0]),
            "attack": spaces.Discrete(self.nActions[0][1])
        }

        playerSpecDict["actions"] = spaces.Dict(actionsDict)
        playerDictP1 = playerSpecDict.copy()
        observationSpaceDict["P1"] = spaces.Dict(playerDictP1)

        actionsDict = {
            "move": spaces.Discrete(self.nActions[1][0]),
            "attack": spaces.Discrete(self.nActions[1][1])
        }

        playerSpecDict["actions"] = spaces.Dict(actionsDict)
        playerDictP2 = playerSpecDict.copy()
        observationSpaceDict["P2"] = spaces.Dict(playerDictP2)

        self.observation_space = spaces.Dict(observationSpaceDict)

    def addObsIntegration(self, frame, data):

        observation = {}
        observation["frame"] = frame

        for iElem, elem in enumerate(["P1", "P2"]):

            playerSpecDict = {}

            # Adding env additional observations (side-specific)
            for k, v in self.addObs.items():

                if k == "stage":
                    continue

                if k[-2:] == elem:
                    knew = "own"+k[:-2]
                else:
                    knew = "opp"+k[:-2]

                playerSpecDict[knew] = data[k]

            actionsDict = {
                "move": data["moveActionP{}".format(iElem+1)],
                "attack": data["attackActionP{}".format(iElem+1)],
            }

            playerSpecDict["actions"] = actionsDict
            observation[elem] = playerSpecDict

        return observation

    # Step the environment
    def step(self, action):

        frame, reward, done, data = self.stepComplete(action)

        observation = self.addObsIntegration(frame, data)

        return observation, reward, done,\
               {"roundDone": data["roundDone"], "stageDone": data["stageDone"],\
                "gameDone": data["gameDone"], "epDone": data["epDone"]}

    # Reset the environment
    def reset(self, **kwargs):

        frame, data = self.resetComplete(**kwargs)

        observation = self.addObsIntegration(frame, data)

        return observation

def makeGymEnv(envPrefix, envSettings, gymSpecSettings, hardCore):

    # Check mandatory parameters
    mandatoryParams = ["gameId"]
    for param in mandatoryParams:
        if param not in envSettings:
            raise RuntimeError("\"{}\" is a mandatory parameter.".format(param))

    # Default to single player mode
    if "player" not in envSettings:
        envSettings["player"] = "Random"
    # Default to not headless mode
    if "headless" not in envSettings:
        envSettings["headless"] = False
    # Retrieve roms path from ENV variables
    if "romsPath" not in envSettings:
        if os.getenv("DIAMBRAROMSPATH") == None:
            raise RuntimeError("\"romsPath\" is a mandatory parameter, either add"+\
                               " it to DIAMBRAROMSPATH environment variable or"+\
                               " specify it via environment settings.")
        else:
            envSettings["romsPath"] = os.getenv("DIAMBRAROMSPATH")

    # Check for OS var DISPLAY
    if os.getenv("DISPLAY") == None:
        print("No DISPLAY environment variable detected, activating HEADLESS mode, and deactivating lockFps if active")
        envSettings["headless"] = True
        envSettings["lockFps"]  = False

    if envSettings["player"] != "P1P2": #1P Mode
        if hardCore:
            env = diambraGymHardCore1P(envPrefix, envSettings, **gymSpecSettings)
        else:
            env = diambraGym1P(envPrefix, envSettings, **gymSpecSettings)
    else: #2P Mode
        if hardCore:
            env = diambraGymHardCore2P(envPrefix, envSettings, **gymSpecSettings)
        else:
            env = diambraGym2P(envPrefix, envSettings, **gymSpecSettings)

    return env, envSettings["player"]
