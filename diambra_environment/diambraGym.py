import sys, platform, os
from pathlib import Path
import numpy as np
import gym
from gym import spaces
from collections import deque
from utils.policies import P2ToP1AddObsMove

import threading
from pipe import *
import time

# DIAMBRA Env Gym
class diambraGym(gym.Env):
    """Diambra Environment gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, env_id, diambraEnvKwargs, P2brain=None, rewNormFac=0.5,
                 continue_game=0.0, show_final=False, gamePads=[None, None],
                 actionSpace=["multiDiscrete", "multiDiscrete"],
                 attackButCombinations=[True, True], actBufLen=12, headless=False):

        self.first = True
        self.continueGame = continue_game
        self.showFinal = show_final
        self.actionSpace = actionSpace
        self.attackButCombinations=attackButCombinations
        self.envData = EnvData()

        # Difficulty
        self.difficulty = diambraEnvKwargs["difficulty"]
        # Number of players (1P or 2P games)
        self.playersNum = "1P"
        if diambraEnvKwargs["player"] == "P1P2":
            self.playersNum = "2P"
        self.pipes_path = os.path.join("/tmp", "DIAMBRA")

        print("Env_id = {}".format(env_id))
        print("Continue value = {}".format(self.continueGame))
        print("Action Spaces = {}".format(self.actionSpace))
        print("Use attack buttons combinations = {}".format(self.attackButCombinations))

        self.ncontinue = 0

        # Launch diambra env core
        # Load library
        libPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diambraEnvLib/libdiambraEnv.so")

        if not libPath:
           print("Unable to find the specified library: {}".format(libPath))
           sys.exit()

        try:
           diambraEnvLib = ctypes.CDLL(libPath)
           print("diambraEnv library successfully loaded")
        except OSError as e:
           print("Unable to load the system C library:", e)
           sys.exit()

        diambraEnv = diambraEnvLib.diambraEnv
        diambraEnv.argtypes = [
                               # INPUTS
                               ctypes.c_wchar_p, # envId_in
                               ctypes.c_wchar_p, # gameId_in
                               ctypes.c_wchar_p, # roms_path_in,
                               ctypes.c_wchar_p, # binary_path_in
                               ctypes.c_wchar_p, # player_in
                               ctypes.c_wchar_p, # charP1_1_in,
                               ctypes.c_wchar_p, # charP1_2_in
                               ctypes.c_wchar_p, # charP2_1_in
                               ctypes.c_wchar_p, # charP2_2_in,
                               ctypes.POINTER(ctypes.c_int), # charOutfits1
                               ctypes.POINTER(ctypes.c_int), # charOutfits2
                               ctypes.POINTER(ctypes.c_int), # difficulty
                               ctypes.POINTER(ctypes.c_int), # mame_diambra_step_ratio,
                               ctypes.POINTER(ctypes.c_bool), # render
                               ctypes.POINTER(ctypes.c_bool), # lock_fps
                               ctypes.POINTER(ctypes.c_bool), # sound
                               ctypes.POINTER(ctypes.c_bool), # disable_keyboard
                               ctypes.c_wchar_p, #pipes_path
                               # OUTPUTS
                               ctypes.POINTER(ctypes.c_int), # fighting
                               ctypes.POINTER(ctypes.c_int), # reward
                               ctypes.POINTER(ctypes.c_int), # ownHealth_1
                               ctypes.POINTER(ctypes.c_int), # ownHealth_2
                               ctypes.POINTER(ctypes.c_int), # oppHealth_1
                               ctypes.POINTER(ctypes.c_int), # oppHealth_2
                               ctypes.POINTER(ctypes.c_int), # ownPosition
                               ctypes.POINTER(ctypes.c_int), # oppPosition
                               ctypes.POINTER(ctypes.c_int), # ownWins
                               ctypes.POINTER(ctypes.c_int), # oppWins
                               ctypes.POINTER(ctypes.c_int), # ownCharacter
                               ctypes.POINTER(ctypes.c_int), # oppCharacter
                               ctypes.POINTER(ctypes.c_int), # stage
                               ctypes.POINTER(ctypes.c_bool), # round_done
                               ctypes.POINTER(ctypes.c_bool), # stage_done
                               ctypes.POINTER(ctypes.c_bool), # game_done
                               ctypes.POINTER(ctypes.c_bool), # ep_done
                               np.ctypeslib.ndpointer(dtype='uint8', ndim=1, flags='C_CONTIGUOUS')] # unsigned char* frame

        diambraEnv.restype = ctypes.c_int

        # Mame path
        mame_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mame/")

        diambraEnvArgs = [env_id, diambraEnvKwargs["gameId"], diambraEnvKwargs["roms_path"],
                   mame_path, diambraEnvKwargs["player"], diambraEnvKwargs["characters"][0][0],
                   diambraEnvKwargs["characters"][0][1], diambraEnvKwargs["characters"][1][0],
                   diambraEnvKwargs["characters"][1][1], (ctypes.c_int)(*[diambraEnvKwargs["charOutfits"][0]]),
                   (ctypes.c_int)(*[diambraEnvKwargs["charOutfits"][1]]),
                   (ctypes.c_int)(*[diambraEnvKwargs["difficulty"]]),
                   (ctypes.c_int)(*[diambraEnvKwargs["mame_diambra_step_ratio"]]), (ctypes.c_bool)(*[diambraEnvKwargs["render"]]),
                   (ctypes.c_bool)(*[diambraEnvKwargs["lock_fps"]]), (ctypes.c_bool)(*[diambraEnvKwargs["sound"]]),
                   (ctypes.c_bool)(*[True]), self.pipes_path, self.envData.fighting, self.envData.reward,
                   self.envData.ownHealth_1, self.envData.ownHealth_2, self.envData.oppHealth_1,
                   self.envData.oppHealth_2, self.envData.ownPosition, self.envData.oppPosition,
                   self.envData.ownWins, self.envData.oppWins, self.envData.ownCharacter,
                   self.envData.oppCharacter, self.envData.stage, self.envData.round_done,
                   self.envData.stage_done, self.envData.game_done, self.envData.ep_done,
                   self.envData.frame]

        if headless:
            os.system("Xvfb :0 -screen 0 800x600x16 +extension RANDR &")
            os.environ["DISPLAY"] = ":0"

        # Launch thread
        self.diambraEnvThread = threading.Thread(target=diambraEnv, args=diambraEnvArgs)
        self.diambraEnvThread.start()

        # Signal file definition
        tmpPathFileName = "pipesTmp" + env_id + ".log"
        tmpPath = Path(self.pipes_path).joinpath(tmpPathFileName)

        # Create Write Pipe
        self.writePipe = Pipe(env_id, "writeToDiambra", "w", self.pipes_path, tmpPath)
        # Create Read Pipe
        self.readPipe = DataPipe(env_id, "readFromDiambra", "r", self.pipes_path, tmpPath)

        # Wait until the fifo file has been created and opened on Diambra Env side
        while (not tmpPath.exists()):
            time.sleep(1)

        time.sleep(2)

        # Open Write Pipe
        self.writePipe.open()
        # Open Read Pipe
        self.readPipe.open()

        # Get Env Info
        envInfo = self.readPipe.read_envInfo()

        # N actions
        self.n_actions_butComb   = [int(envInfo[0]), int(envInfo[1])]
        self.n_actions_noButComb = [int(envInfo[2]), int(envInfo[3])]
        # N actions
        self.n_actions = [self.n_actions_butComb, self.n_actions_butComb]
        for idx in range(2):
            if not self.attackButCombinations[idx]:
                self.n_actions[idx] = self.n_actions_noButComb

        # Frame height, width and channel dimensions
        self.hwc_dim = [int(envInfo[4]), int(envInfo[5]), int(envInfo[6])]
        self.envData.setFrameSize(self.hwc_dim)

        # Maximum players health
        self.max_health = int(envInfo[7])

        # Maximum number of stages (1P game vs COM)
        self.max_stage = int(envInfo[8])

        # Number of characters of the game
        self.numberOfCharacters = int(envInfo[9])
        # Characters names list
        self.charNames = []
        for idx in range(10, 10 + self.numberOfCharacters):
            self.charNames.append(envInfo[idx])

        currentIdx = 10 + self.numberOfCharacters

        # Action list
        moveList = ()
        for idx in range(currentIdx, currentIdx + self.n_actions_butComb[0]):
            moveList += (envInfo[idx],)

        currentIdx += self.n_actions_butComb[0]

        attackList = ()
        for idx in range(currentIdx, currentIdx + self.n_actions_butComb[1]):
            attackList += (envInfo[idx],)

        currentIdx += self.n_actions_butComb[1]

        self.actionList = (moveList, attackList)

        # Action dict
        moveDict = {}
        for idx in range(currentIdx, currentIdx + 2*self.n_actions_butComb[0], 2):
            moveDict[int(envInfo[idx])] = envInfo[idx+1]

        currentIdx += 2*self.n_actions_butComb[0]

        attackDict = {}
        for idx in range(currentIdx, currentIdx + 2*self.n_actions_butComb[1], 2):
            attackDict[int(envInfo[idx])] = envInfo[idx+1]

        self.print_actions_dict = [moveDict, attackDict]

        # Initialize frame dims inside read pipe
        self.readPipe.setFrameSize(self.hwc_dim)

        # Reward normalization factor with respect to max health
        self.rewNormFac = rewNormFac

        # P2 action logic (for AIvsHUM and AIvsAI training)
        self.p2Brain = P2brain

        # Last obs stored (for AIvsAI training)
        self.lastObs = None

        # Define action and observation space
        # They must be gym.spaces objects
        # We check only first element of self.actionSpace since for now only 1P
        # training is supported and here defining the action space is for training

        if self.actionSpace[0] == "multiDiscrete":
            # MultiDiscrete actions:
            # - Arrows -> One discrete set
            # - Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.MultiDiscrete(self.n_actions[0])
            print("Using MultiDiscrete action space")
        elif self.actionSpace[0] == "discrete":
            # Discrete actions:
            # - Arrows U Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.Discrete(self.n_actions[0][0] + self.n_actions[0][1] - 1)
            print("Using Discrete action space")
        else:
            raise Exception("Not recognized action space: {}".format(self.actionSpace[0]))

        # Image as input:
        self.observation_space = spaces.Box(low=0, high=255,
                                        shape=(self.hwc_dim[0], self.hwc_dim[1], self.hwc_dim[2]), dtype=np.uint8)

        # Saving both action spaces
        self.action_spaces = [None, None]
        for idx in range(2):
            if self.actionSpace[idx] == "multiDiscrete":
                self.action_spaces[idx] = spaces.MultiDiscrete(self.n_actions[idx])
            else:
                self.action_spaces[idx] = spaces.Discrete(self.n_actions[idx][0] + self.n_actions[idx][1] - 1)

        self.actBufLen = actBufLen
        self.clearActBuf()

    # Return min max rewards for the environment
    def minMaxRew(self):
        coeff = 1.0/self.rewNormFac
        if self.playersNum == "2P":
            return (-2*coeff, 2*coeff)
        else:
            return (-coeff*(self.max_stage-1)-2*coeff, self.max_stage*2*coeff)

    # Return actions dict
    def print_actions_dict(self):
        return self.print_actions_dict

    # Return env action list
    def actionList(self):
        return self.actionList

    # Clear actions buffers
    def clearActBuf(self):
        self.ownMovActBuf = deque([0 for i in range(self.actBufLen)], maxlen = self.actBufLen)
        self.ownAttActBuf = deque([0 for i in range(self.actBufLen)], maxlen = self.actBufLen)
        self.oppMovActBuf = deque([0 for i in range(self.actBufLen)], maxlen = self.actBufLen)
        self.oppAttActBuf = deque([0 for i in range(self.actBufLen)], maxlen = self.actBufLen)

    # Discrete to multidiscrete action conversion
    def discreteToMultiDiscreteAction(self, action):

        movAct = 0
        attAct = 0

        if action <= self.n_actions[0][0] - 1:
            # Move action or no action
            movAct = action # For example, for DOA++ this can be 0 - 8
        else:
            # Attack action
            attAct = action - self.n_actions[0][0] + 1 # For example, for DOA++ this can be 1 - 7

        return movAct, attAct

    # Step the environment
    def step(self, action):

        # Actions initialization
        ownMovAct = 0
        ownAttAct = 0
        oppMovAct = 0
        oppAttAct = 0

        # Defining move and attack actions P1/P2 as a function of actionSpace
        if self.actionSpace[0] == "multiDiscrete": # 1P MultiDiscrete Action Space

            # 1P
            ownMovAct = action[0]
            ownAttAct = action[1]

            # 2P
            if self.playersNum == "2P":

                if self.actionSpace[1] == "multiDiscrete": # 2P MultiDiscrete Action Space

                    if self.p2Brain == None:
                        oppMovAct = action[2]
                        oppAttAct = action[3]
                    else:
                        if self.p2Brain.id == "rl":
                            self.lastObs[:,:,-1] = P2ToP1AddObsMove(self.lastObs[:,:,-1])
                        [oppMovAct, oppAttAct], _ = self.p2Brain.act(self.lastObs)

                else: # 2P Discrete Action Space

                    if self.p2Brain == None:
                        oppMovAct, oppAttAct = self.discreteToMultiDiscreteAction(action[2])
                    else:
                        if self.p2Brain.id == "rl":
                            self.lastObs[:,:,-1] = P2ToP1AddObsMove(self.lastObs[:,:,-1])
                        brainActions, _ = self.p2Brain.act(self.lastObs)
                        oppMovAct, oppAttAct = self.discreteToMultiDiscreteAction(brainActions)

        else: # 1P Discrete Action Space

            if self.playersNum == "1P":

                # 1P
                # Discrete to multidiscrete conversion
                ownMovAct, ownAttAct = self.discreteToMultiDiscreteAction(action)

            else:

                # 1P
                # Discrete to multidiscrete conversion
                ownMovAct, ownAttAct = self.discreteToMultiDiscreteAction(action[0])

                # 2P
                if self.actionSpace[1] == "multiDiscrete": # 2P MultiDiscrete Action Space

                    if self.p2Brain == None:
                        oppMovAct = action[1]
                        oppAttAct = action[2]
                    else:
                        if self.p2Brain.id == "rl":
                            self.lastObs[:,:,-1] = P2ToP1AddObsMove(self.lastObs[:,:,-1])
                        [oppMovAct, oppAttAct], _ = self.p2Brain.act(self.lastObs)

                else: # 2P Discrete Action Space

                    if self.p2Brain == None:
                        oppMovAct, oppAttAct = self.discreteToMultiDiscreteAction(action[1])
                    else:
                        if self.p2Brain.id == "rl":
                            self.lastObs[:,:,-1] = P2ToP1AddObsMove(self.lastObs[:,:,-1])
                        brainActions, _ = self.p2Brain.act(self.lastObs)
                        oppMovAct, oppAttAct = self.discreteToMultiDiscreteAction(brainActions)

        if self.playersNum == "2P":
            self.writePipe.sendComm(diambraEnvComm["step"], ownMovAct, ownAttAct, oppMovAct, oppAttAct)
            self.readPipe.readFlag()
            observation, data = self.envData.read_data()

            reward            = data["reward"]
            round_done        = data["round_done"]
            done              = data["game_done"]
            stage_done        = False
            game_done         = done
            data["ep_done"]   = done
        else:
            self.writePipe.sendComm(diambraEnvComm["step"], ownMovAct, ownAttAct)
            self.readPipe.readFlag()
            observation, data = self.envData.read_data()
            reward            = data["reward"]
            round_done        = data["round_done"]
            done              = data["ep_done"]
            stage_done        = data["stage_done"]
            game_done         = data["game_done"]

        # Extend the action buffer
        self.ownMovActBuf.extend([ownMovAct])
        self.ownAttActBuf.extend([ownAttAct])
        if self.playersNum == "2P":
            self.oppMovActBuf.extend([oppMovAct])
            self.oppAttActBuf.extend([oppAttAct])

        if done:
            if self.showFinal:
                self.writePipe.sendComm(diambraEnvComm["show_final"])

            print("Episode done")
        elif game_done:
            self.clearActBuf()

            # Continuing rule:
            continueFlag = True
            if self.continueGame < 0.0:
                if self.ncontinue < int(abs(self.continueGame)):
                    self.ncontinue += 1
                    continueFlag = True
                else:
                    continueFlag = False
            elif self.continueGame <= 1.0:
                continueFlag = np.random.choice([True, False], p=[self.continueGame, 1.0 - self.continueGame])
            else:
                raise ValueError('continue_game must be <= 1.0')

            if continueFlag:
                print("Game done, continuing ...")
                self.writePipe.sendComm(diambraEnvComm["continue_game"])
                self.readPipe.readFlag()
                oldRew = data["reward"]
                observation, data = self.envData.read_data()
                data["reward"] = oldRew
            else:
                print("Episode done")
                data["ep_done"] = True
                done = True
        elif stage_done:
            print("Stage done")
            self.clearActBuf()
            self.writePipe.sendComm(diambraEnvComm["next_stage"])
            self.readPipe.readFlag()
            oldRew = data["reward"]
            observation, data = self.envData.read_data()
            data["reward"] = oldRew
        elif round_done:
            print("Round done")
            self.clearActBuf()
            self.writePipe.sendComm(diambraEnvComm["next_round"])
            self.readPipe.readFlag()
            oldRew = data["reward"]
            observation, data = self.envData.read_data()
            data["reward"] = oldRew

        # Add the action buffer to the step data
        data["actionsBufP1"] = [self.ownMovActBuf, self.ownAttActBuf]
        if self.playersNum == "2P":
            data["actionsBufP2"] = [self.oppMovActBuf, self.oppAttActBuf]

        return observation, reward, done, data

    # Resetting the environment
    def reset(self):

        self.clearActBuf()
        self.ncontinue = 0

        if self.first:
            self.first = False
            self.writePipe.sendComm(diambraEnvComm["start"])
        else:
            self.writePipe.sendComm(diambraEnvComm["new_game"])

        self.readPipe.readFlag()
        observation, data = self.envData.read_data()

        # Deactivating showFinal for 2P Env (Needed to do it here after Env start)
        if self.playersNum == "2P":
            self.showFinal = False

        return observation

    # Rendering the environment
    def render(self, mode='human'):
        pass

    # Closing the environment
    def close(self):
        self.first = True
        self.writePipe.sendComm(diambraEnvComm["close"])

        # Close pipes
        self.writePipe.close()
        self.readPipe.close()

        self.diambraEnvThread.join(timeout=30)
        if self.diambraEnvThread.isAlive():
            error = "Failed to close DIAMBRA Env process"
            raise EnvironmentError(error)
