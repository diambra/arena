import sys, platform, os
import numpy as np
import gym
from gym import spaces
import pickle, bz2
import copy
import cv2
from utils.policies import P2ToP1AddObsMove

from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines.common import set_global_seeds
from stable_baselines.bench import Monitor

class diambraImitationLearning(gym.Env):
    """DiambraMame Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, hwc_dim, action_space, n_actions, trajFilesList, rank, totalCpus):
        super(diambraImitationLearning, self).__init__()

        # Observation and action space
        self.obsH = hwc_dim[0]
        self.obsW = hwc_dim[1]
        self.obsNChannels = hwc_dim[2]
        self.n_actions = n_actions
        self.actionSpace = action_space

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
            self.action_space = spaces.MultiDiscrete(self.n_actions)
            print("Using MultiDiscrete action space")
        elif self.actionSpace == "discrete":
            # Discrete actions:
            # - Arrows U Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
            print("Using Discrete action space")
        else:
            raise Exception("Not recognized action space: {}".format(self.actionSpace))

        # Image as input:
        self.observation_space = spaces.Box(low=0.0, high=1.0,
                                            shape=(self.obsH, self.obsW, self.obsNChannels),
                                            dtype=np.float32)

        # List of RL trajectories files
        self.trajFilesList = trajFilesList

        # CPU rank for this env instance
        self.rank = rank
        self.totalCpus = totalCpus

        # Check for number of files
        if self.totalCpus > len(self.trajFilesList):
            raise Exception("Number of requested CPUs > number of recorded experience available files")

        # Idx of trajectory file to read
        self.trajIdx = self.rank
        self.RLTrajDict = None

        # If run out of examples
        self.exhausted = False

        # Reset flag
        self.nReset = 0

        # Observations shift counter (for new round/stage/game)
        self.shiftCounter = 1

    # Discrete to multidiscrete action conversion
    def discreteToMultiDiscreteAction(self, action):

        movAct = 0
        attAct = 0

        if action <= self.n_actions[0] - 1:
            # Move action or no action
            movAct = action # For example, for DOA++ this can be 0 - 8
        else:
            # Attack action
            attAct = action - self.n_actions[0] + 1 # For example, for DOA++ this can be 1 - 7

        return movAct, attAct

    # Print Episode summary
    def trajSummary(self):

        print(self.RLTrajDict.keys())

        print("Ep. length = {}".format(self.RLTrajDict["epLen"] ))

        for key, value in self.RLTrajDict.items():
            if type(value) == list and len(value) > 2:
                print("len({}): {}".format(key, len(value)))
            else:
                print("{} : {}".format(key, value))

    # Step the environment
    def step(self, dummyAction):

        # Done retrieval
        done = False
        if self.stepIdx == self.RLTrajDict["epLen"] - 1:
            done = True

        # Done flags retrieval
        doneFlags = self.RLTrajDict["doneFlags"][self.stepIdx]

        if (doneFlags[0] or doneFlags[1] or doneFlags[2]) and not done:
            self.shiftCounter += self.obsNChannels-2

        # Observation retrieval
        observation = np.zeros((self.obsH, self.obsW, self.obsNChannels))
        for iFrame in range(self.obsNChannels-1):
            observation[:,:,iFrame] = self.RLTrajDict["frames"][self.stepIdx +
                                                                self.shiftCounter + iFrame]
        observation[:,:,self.obsNChannels-1] = self.RLTrajDict["addObs"][self.stepIdx + 1]

        # Storing last observation for rendering
        self.lastObs = observation[:,:,self.obsNChannels-2]

        # Reward retrieval
        reward = self.RLTrajDict["rewards"][self.stepIdx]

        # Action retrieval
        action = self.RLTrajDict["actions"][self.stepIdx]
        if (self.actionSpace == "discrete"):
            actionNew = self.discreteToMultiDiscreteAction(action)
        else:
            actionNew = action

        action = [actionNew[0], actionNew[1]]
        info = {}
        info["action"] = action

        if np.any(done):
            print("(Rank {}) Episode done".format(self.rank))

        # Update step idx
        self.stepIdx += 1

        return observation, reward, done, info

    # Resetting the environment
    def reset(self):

        # Reset run step
        self.stepIdx = 0

        # Observations shift counter (for new round/stage/game)
        self.shiftCounter = 1

        # Manage ignoreP2 flag for recorded P1P2 trajectory (e.g. when HUMvsAI)
        if self.nReset != 0 and self.RLTrajDict["ignoreP2"] == 1:

            print("Skipping P2 trajectory for 2P games (e.g. HUMvsAI)")
            # Resetting nReset
            self.nReset = 0
            # Move traj idx to the next to be read
            self.trajIdx += self.totalCpus

        # Check if run out of traj files
        if self.trajIdx >= len(self.trajFilesList):
            print("(Rank {}) Resetting env".format(self.rank))
            self.exhausted = True
            return np.zeros((self.obsH, self.obsW, self.obsNChannels))

        if self.nReset == 0:
            RLTrajFile = self.trajFilesList[self.trajIdx]

            # Read compressed RL Traj file
            infile = bz2.BZ2File(RLTrajFile, 'r')
            self.RLTrajDict = pickle.load(infile)
            infile.close()

            # Storing env info
            self.nChars = len(self.RLTrajDict["charNames"])
            self.charNames = self.RLTrajDict["charNames"]
            self.actBufLen = self.RLTrajDict["actBufLen"]
            self.playersNum = self.RLTrajDict["playersNum"]
            assert self.n_actions == self.RLTrajDict["nActions"],\
                "Recorded episode has {} actions".format(self.RLTrajDict["nActions"])
            assert self.actionSpace == self.RLTrajDict["actionSpace"],\
                "Recorded episode has {} action space".format(self.RLTrajDict["actionSpace"])

        if self.playersNum == "2P": # e.g. HUMvsHUM

            print("Two players RL trajectory")

            if self.nReset == 0:
            # First reset for this trajectory

                print("Loading P1 data for 2P trajectory")

                # Generate P2 Experience from P1 one
                self.generateP2ExperienceFromP1()

                # Update reset counter
                self.nReset += 1

            else:
            # Second reset for this trajectory

                print("Loading P2 data for 2P trajectory")

                # OverWrite P1 RL trajectory with the one calculated for P2
                self.RLTrajDict = self.RLTrajDictP2

                # Reset reset counter
                self.nReset = 0

                # Move traj idx to the next to be read
                self.trajIdx += self.totalCpus

        else:

            print("One player RL trajectory")

            # Move traj idx to the next to be read
            self.trajIdx += self.totalCpus

        # Reset observation retrieval
        observation = np.zeros((self.obsH, self.obsW, self.obsNChannels))
        for iFrame in range(self.obsNChannels-1):
            observation[:,:,iFrame] = self.RLTrajDict["frames"][iFrame]
        observation[:,:,self.obsNChannels-1] = self.RLTrajDict["addObs"][0]

        # Storing last observation for rendering
        self.lastObs = observation[:,:,self.obsNChannels-2]

        return observation

    # Generate P2 Experience from P1 one
    def generateP2ExperienceFromP1(self):

        # Copy P1 Trajectory
        self.RLTrajDictP2 = copy.deepcopy(self.RLTrajDict)

        # Process Additiona Obs for P2 (copy them in P1 position)
        newAddObsList = []

        for addObs in self.RLTrajDictP2["addObs"]:
            newAddObs = P2ToP1AddObsMove(addObs)
            newAddObsList.append(newAddObs)

        self.RLTrajDictP2["addObs"] = newAddObsList

        # For each step, convert P1 into P2 experience
        for idx in range(self.RLTrajDict["epLen"]):

            # Rewards (inverting sign)
            self.RLTrajDictP2["rewards"][idx] = -self.RLTrajDict["rewards"][idx]

            # Actions (inverting positions)
            self.RLTrajDictP2["actions"][idx] = [self.RLTrajDict["actions"][idx][2],
                                                 self.RLTrajDict["actions"][idx][3]]

    # Rendering the environment
    def render(self, mode='human'):

        if mode == "human":
            windowName = "Diambra Imitation Learning Environment"
            cv2.namedWindow(windowName,cv2.WINDOW_GUI_NORMAL)
            cv2.imshow(windowName, self.lastObs)
            cv2.waitKey(1)
        elif mode == "rgb_array":
            output = np.expand_dims(self.lastObs, axis=2)
            return output

# Function to vectorialize envs
def make_diambra_imitationLearning_env(diambraIL, diambraIL_kwargs, seed=0,
                                       allow_early_resets=True):
    """
    Utility function for multiprocessed env.

    :param diambraIL_kwargs: (dict) kwargs for Diambra IL env
    """

    num_env = diambraIL_kwargs["totalCpus"]

    def make_env(rank):
        def _thunk():

            # Create log dir
            log_dir = "tmp"+str(rank)+"/"
            os.makedirs(log_dir, exist_ok=True)
            env = diambraIL(**diambraIL_kwargs, rank=rank)
            env = Monitor(env, log_dir, allow_early_resets=allow_early_resets)
            return env
        set_global_seeds(seed)
        return _thunk

    # When using one environment, no need to start subprocesses
    if num_env == 1:
        return DummyVecEnv([make_env(i) for i in range(num_env)])

    return SubprocVecEnv([make_env(i) for i in range(num_env)])
