import sys, platform, os
import numpy as np
import gym
from gym import spaces
import pickle, bz2
import copy
import cv2
from diambraArena.gymUtils import standardDictToGymObsDict, discreteToMultiDiscreteAction

# Diambra imitation learning environment
class diambraImitationLearningBase(gym.Env):
    """DiambraMame Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, trajFilesList, rank=0, totalCpus=1):
        super(diambraImitationLearningBase, self).__init__()

        # Check for number of files
        if totalCpus > len(trajFilesList):
            raise Exception("Number of requested CPUs > number of recorded experience available files")

        # List of RL trajectories files
        self.trajFilesList = trajFilesList

        # CPU rank for this env instance
        self.rank = rank
        self.totalCpus = totalCpus

        # Idx of trajectory file to read
        self.trajIdx = self.rank
        self.RLTrajDict = None

        # Open the first file to retrieve env info: ---
        TmpRLTrajFile = self.trajFilesList[self.trajIdx]

        # Read compressed RL Traj file
        infile = bz2.BZ2File(TmpRLTrajFile, 'r')
        self.TmpRLTrajDict = pickle.load(infile)
        infile.close()

        # Observation and action space
        self.frameH          = self.TmpRLTrajDict["frameShp"][0]
        self.frameW          = self.TmpRLTrajDict["frameShp"][1]
        self.frameNChannels  = self.TmpRLTrajDict["frameShp"][2]
        self.nActions        = self.TmpRLTrajDict["nActions"]
        self.actionSpace     = self.TmpRLTrajDict["actionSpace"]
        # ---

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
            self.action_space = spaces.MultiDiscrete(self.nActions)
            print("Using MultiDiscrete action space")
        elif self.actionSpace == "discrete":
            # Discrete actions:
            # - Arrows U Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.Discrete(self.nActions[0] + self.nActions[1] - 1)
            print("Using Discrete action space")
        else:
            raise Exception("Not recognized action space: {}".format(self.actionSpace))

        # If run out of examples
        self.exhausted = False

        # Reset flag
        self.nReset = 0

        # Observations shift counter (for new round/stage/game)
        self.shiftCounter = 1

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
            self.shiftCounter += self.frameNChannels-1

        # Observation retrieval
        observation = self.obsRetrieval()

        # Reward retrieval
        reward = self.RLTrajDict["rewards"][self.stepIdx]

        # Action retrieval
        action = self.RLTrajDict["actions"][self.stepIdx]
        if (self.actionSpace == "discrete"):
            actionNew = discreteToMultiDiscreteAction(action, self.nActions[0])
        else:
            actionNew = action

        action = [actionNew[0], actionNew[1]]
        info = {}
        info["action"] = action
        info["roundDone"] = doneFlags[0]
        info["stageDone"] = doneFlags[1]
        info["gameDone"] = doneFlags[2]
        info["episodeDone"] = doneFlags[3]

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
            observation = {}
            observation = self.blackScreen(observation)
            return observation

        if self.nReset == 0:
            RLTrajFile = self.trajFilesList[self.trajIdx]

            # Read compressed RL Traj file
            infile = bz2.BZ2File(RLTrajFile, 'r')
            self.RLTrajDict = pickle.load(infile)
            infile.close()

            # Storing env info
            self.nChars = len(self.RLTrajDict["charNames"])
            self.charNames = self.RLTrajDict["charNames"]
            self.nActionsStack = self.RLTrajDict["nActionsStack"]
            self.playerSide = self.RLTrajDict["playerSide"]
            assert self.nActions == self.RLTrajDict["nActions"],\
                "Recorded episode has {} actions".format(self.RLTrajDict["nActions"])
            assert self.actionSpace == self.RLTrajDict["actionSpace"],\
                "Recorded episode has {} action space".format(self.RLTrajDict["actionSpace"])

        if self.playerSide == "P1P2":

            print("Two players RL trajectory")

            if self.nReset == 0:
            # First reset for this trajectory

                print("Loading P1 data for 2P trajectory")

                # Generate P2 Experience from P1 one
                self.generateP2ExperienceFromP1()

                # For each step, isolate P1 actions from P1P2 experience
                for idx in range(self.RLTrajDict["epLen"]):
                    # Actions (inverting positions)
                    if (self.actionSpace == "discrete"):
                        self.RLTrajDict["actions"][idx] = self.RLTrajDict["actions"][idx][0]
                    else:
                        self.RLTrajDict["actions"][idx] = [self.RLTrajDict["actions"][idx][0],
                                                     self.RLTrajDict["actions"][idx][1]]

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

        # Observation retrieval
        observation = self.obsRetrieval(resetShift=1)

        return observation

    # Generate P2 Experience from P1 one
    def generateP2ExperienceFromP1(self):

        # Copy P1 Trajectory
        self.RLTrajDictP2 = copy.deepcopy(self.RLTrajDict)

        # For each step, convert P1 into P2 experience
        for idx in range(self.RLTrajDict["epLen"]):

            # Rewards (inverting sign)
            self.RLTrajDictP2["rewards"][idx] = -self.RLTrajDict["rewards"][idx]

            # Actions (inverting positions)
            if (self.actionSpace == "discrete"):
                self.RLTrajDictP2["actions"][idx] = self.RLTrajDict["actions"][idx][1]
            else:
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

# Diambra imitation learning environment
class diambraImitationLearningHardCore(diambraImitationLearningBase):
    def __init__(self, trajFilesList, rank=0, totalCpus=1):
        super().__init__(trajFilesList, rank, totalCpus)

        # Observation space
        playerSide     = self.TmpRLTrajDict["playerSide"]
        obsSpaceBounds = self.TmpRLTrajDict["obsSpaceBounds"]

        # Create the observation space
        self.observation_space = spaces.Box(low=obsSpaceBounds[0], high=obsSpaceBounds[1],
                                            shape=(self.frameH, self.frameW, self.frameNChannels),
                                            dtype=np.float32)

    # Specific observation retrieval
    def obsRetrieval(self, resetShift=0):
        # Observation retrieval
        observation = np.zeros((self.frameH, self.frameW, self.frameNChannels))
        for iFrame in range(self.frameNChannels):
            observation[:,:,iFrame] = self.RLTrajDict["frames"][self.stepIdx +
                                                               self.shiftCounter + iFrame - resetShift]
        # Storing last observation for rendering
        self.lastObs = observation[:,:,self.frameNChannels-1]

        return observation

    # Black screen
    def blackScreen(self, observation):

       observation = np.zeros((self.frameH, self.frameW, self.frameNChannels))

       return observation

# Diambra imitation learning environment
class diambraImitationLearning(diambraImitationLearningBase):
    def __init__(self, trajFilesList, rank=0, totalCpus=1):
        super().__init__( trajFilesList, rank, totalCpus)

        # Observation space
        playerSide           = self.TmpRLTrajDict["playerSide"]
        self.observationSpaceDict = self.TmpRLTrajDict["observationSpaceDict"]
        # Remove P2 sub space from Obs Space
        if playerSide == "P1P2":
            self.observationSpaceDict.pop("P2")

        # Create the observation space
        self.observation_space = standardDictToGymObsDict(self.observationSpaceDict)

    # Specific observation retrieval
    def obsRetrieval(self, resetShift=0):
        # Observation retrieval
        observation = self.RLTrajDict["addObs"][self.stepIdx + 1 - resetShift].copy()

        # Frame
        observation["frame"] = np.zeros((self.frameH, self.frameW, self.frameNChannels))
        for iFrame in range(self.frameNChannels):
            observation["frame"][:,:,iFrame] = self.RLTrajDict["frames"][self.stepIdx +
                                                                self.shiftCounter + iFrame -resetShift]
        # Storing last observation for rendering
        self.lastObs = observation["frame"][:,:,self.frameNChannels-1]

        return observation

    # Black screen
    def blackScreen(self, observation):

       observation["frame"] = np.zeros((self.frameH, self.frameW, self.frameNChannels))

       return observation

    # Generate P2 Experience from P1 one
    def generateP2ExperienceFromP1(self):

        super().generateP2ExperienceFromP1()

        # Process Additiona Obs for P2 (copy them in P1 position)
        for addObs in self.RLTrajDictP2["addObs"]:
            addObs.pop("P1")
            addObs["P1"] = addObs.pop("P2")
            addObs["stage"] = 0

        # Remove P2 info from P1 Observation
        for addObs in self.RLTrajDict["addObs"]:
            addObs.pop("P2")
            addObs["stage"] = 0

