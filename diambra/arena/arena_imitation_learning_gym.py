import numpy as np
import gym
from gym import spaces
import pickle
import bz2
import copy
import cv2
from diambra.arena.utils.gym_utils import standard_dict_to_gym_obs_dict,\
    discrete_to_multi_discrete_action

# Diambra imitation learning environment


class ImitationLearningBase(gym.Env):
    """Diambra Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, traj_files_list, rank=0, total_cpus=1):
        super(ImitationLearningBase, self).__init__()

        # Check for number of files
        if total_cpus > len(traj_files_list):
            raise Exception(
                "Number of requested CPUs > number of "
                "recorded experience available files")

        # List of RL trajectories files
        self.traj_files_list = traj_files_list

        # CPU rank for this env instance
        self.rank = rank
        self.total_cpus = total_cpus

        # Idx of trajectory file to read
        self.trajIdx = self.rank
        self.RLTrajDict = None

        # Open the first file to retrieve env info: ---
        tmp_rl_traj_file = self.traj_files_list[self.trajIdx]

        # Read compressed RL Traj file
        infile = bz2.BZ2File(tmp_rl_traj_file, 'r')
        self.TmpRLTrajDict = pickle.load(infile)
        infile.close()

        # Observation and action space
        self.frame_h = self.TmpRLTrajDict["frameShp"][0]
        self.frameW = self.TmpRLTrajDict["frameShp"][1]
        self.frameNChannels = self.TmpRLTrajDict["frameShp"][2]
        self.nActions = self.TmpRLTrajDict["nActions"]
        self.actionSpace = self.TmpRLTrajDict["actionSpace"]
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
            self.action_space = spaces.Discrete(
                self.nActions[0] + self.nActions[1] - 1)
            print("Using Discrete action space")
        else:
            raise Exception(
                "Not recognized action space: {}".format(self.actionSpace))

        # If run out of examples
        self.exhausted = False

        # Reset flag
        self.nReset = 0

        # Observations shift counter (for new round/stage/game)
        self.shiftCounter = 1

    # Print Episode summary
    def traj_summary(self):

        print(self.RLTrajDict.keys())

        print("Ep. length = {}".format(self.RLTrajDict["epLen"]))

        for key, value in self.RLTrajDict.items():
            if type(value) == list and len(value) > 2:
                print("len({}): {}".format(key, len(value)))
            else:
                print("{} : {}".format(key, value))

    # Step the environment
    def step(self, dummy_action):

        # Done retrieval
        done = False
        if self.stepIdx == self.RLTrajDict["epLen"] - 1:
            done = True

        # Done flags retrieval
        done_flags = self.RLTrajDict["done_flags"][self.stepIdx]

        if (done_flags[0] or done_flags[1] or done_flags[2]) and not done:
            self.shiftCounter += self.frameNChannels-1

        # Observation retrieval
        observation = self.obs_retrieval()

        # Reward retrieval
        reward = self.RLTrajDict["rewards"][self.stepIdx]

        # Action retrieval
        action = self.RLTrajDict["actions"][self.stepIdx]
        if (self.actionSpace == "discrete"):
            action_new = discreteToMultiDiscreteAction(action, self.nActions[0])
        else:
            action_new = action

        action = [action_new[0], action_new[1]]
        info = {}
        info["action"] = action
        info["roundDone"] = done_flags[0]
        info["stageDone"] = done_flags[1]
        info["gameDone"] = done_flags[2]
        info["episodeDone"] = done_flags[3]

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
            self.trajIdx += self.total_cpus

        # Check if run out of traj files
        if self.trajIdx >= len(self.traj_files_list):
            print("(Rank {}) Resetting env".format(self.rank))
            self.exhausted = True
            observation = {}
            observation = self.black_screen(observation)
            return observation

        if self.nReset == 0:
            rl_traj_file = self.traj_files_list[self.trajIdx]

            # Read compressed RL Traj file
            infile = bz2.BZ2File(rl_traj_file, 'r')
            self.RLTrajDict = pickle.load(infile)
            infile.close()

            # Storing env info
            self.nChars = len(self.RLTrajDict["charNames"])
            self.charNames = self.RLTrajDict["charNames"]
            self.nActionsStack = self.RLTrajDict["nActionsStack"]
            self.player_side = self.RLTrajDict["player_side"]
            assert self.nActions == self.RLTrajDict["nActions"],\
                "Recorded episode has {} actions".format(
                    self.RLTrajDict["nActions"])
            assert self.actionSpace == self.RLTrajDict["actionSpace"],\
                "Recorded episode has {} action space".format(
                    self.RLTrajDict["actionSpace"])

        if self.player_side == "P1P2":

            print("Two players RL trajectory")

            if self.nReset == 0:
                # First reset for this trajectory

                print("Loading P1 data for 2P trajectory")

                # Generate P2 Experience from P1 one
                self.generate_p2_experience_from_p1()

                # For each step, isolate P1 actions from P1P2 experience
                for idx in range(self.RLTrajDict["epLen"]):
                    # Actions (inverting sides)
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
                self.trajIdx += self.total_cpus

        else:

            print("One player RL trajectory")

            # Move traj idx to the next to be read
            self.trajIdx += self.total_cpus

        # Observation retrieval
        observation = self.obs_retrieval(reset_shift=1)

        return observation

    # Generate P2 Experience from P1 one
    def generate_p2_experience_from_p1(self):

        # Copy P1 Trajectory
        self.RLTrajDictP2 = copy.deepcopy(self.RLTrajDict)

        # For each step, convert P1 into P2 experience
        for idx in range(self.RLTrajDict["epLen"]):

            # Rewards (inverting sign)
            self.RLTrajDictP2["rewards"][idx] = - \
                self.RLTrajDict["rewards"][idx]

            # Actions (inverting sides)
            if (self.actionSpace == "discrete"):
                self.RLTrajDictP2["actions"][idx] = self.RLTrajDict["actions"][idx][1]
            else:
                self.RLTrajDictP2["actions"][idx] = [self.RLTrajDict["actions"][idx][2],
                                                     self.RLTrajDict["actions"][idx][3]]

    # Rendering the environment
    def render(self, mode='human'):

        if mode == "human":
            window_name = "Diambra Imitation Learning Environment - {}".format(
                self.rank)
            cv2.namedWindow(window_name, cv2.WINDOW_GUI_NORMAL)
            cv2.imshow(window_name, self.lastObs)
            cv2.waitKey(1)
        elif mode == "rgb_array":
            output = np.expand_dims(self.lastObs, axis=2)
            return output

# Diambra imitation learning environment


class ImitationLearningHardCore(ImitationLearningBase):
    def __init__(self, traj_files_list, rank=0, total_cpus=1):
        super().__init__(traj_files_list, rank, total_cpus)

        # Observation space
        obs_space_bounds = self.TmpRLTrajDict["obs_space_bounds"]

        # Create the observation space
        self.observation_space = spaces.Box(low=obs_space_bounds[0],
                                            high=obs_space_bounds[1],
                                            shape=(self.frame_h, self.frameW,
                                                   self.frameNChannels),
                                            dtype=np.float32)

    # Specific observation retrieval
    def obs_retrieval(self, reset_shift=0):
        # Observation retrieval
        observation = np.zeros((self.frame_h, self.frameW, self.frameNChannels))
        for iframe in range(self.frameNChannels):
            observation[:, :, iframe] = self.RLTrajDict["frames"][self.stepIdx +
                                                                  self.shiftCounter + iframe - reset_shift]
        # Storing last observation for rendering
        self.lastObs = observation[:, :, self.frameNChannels-1]

        return observation

    # Black screen
    def black_screen(self, observation):

        observation = np.zeros((self.frame_h, self.frameW, self.frameNChannels))

        return observation

# Diambra imitation learning environment


class ImitationLearning(ImitationLearningBase):
    def __init__(self, traj_files_list, rank=0, total_cpus=1):
        super().__init__(traj_files_list, rank, total_cpus)

        # Observation space
        player_side = self.TmpRLTrajDict["player_side"]
        self.observationSpaceDict = self.TmpRLTrajDict["observationSpaceDict"]
        # Remove P2 sub space from Obs Space
        if player_side == "P1P2":
            self.observationSpaceDict.pop("P2")

        # Create the observation space
        self.observation_space = standardDictToGymObsDict(
            self.observationSpaceDict)

    # Specific observation retrieval
    def obs_retrieval(self, reset_shift=0):
        # Observation retrieval
        observation = self.RLTrajDict["add_obs"][self.stepIdx +
                                                 1 - reset_shift].copy()

        # Frame
        observation["frame"] = np.zeros(
            (self.frame_h, self.frameW, self.frameNChannels))
        for iframe in range(self.frameNChannels):
            observation["frame"][:, :, iframe] = self.RLTrajDict["frames"][self.stepIdx +
                                                                           self.shiftCounter + iframe - reset_shift]
        # Storing last observation for rendering
        self.lastObs = observation["frame"][:, :, self.frameNChannels-1]

        return observation

    # Black screen
    def black_screen(self, observation):

        observation["frame"] = np.zeros(
            (self.frame_h, self.frameW, self.frameNChannels))

        return observation

    # Generate P2 Experience from P1 one
    def generate_p2_experience_from_p1(self):

        super().generate_p2_experience_from_p1()

        # Process Additiona Obs for P2 (copy them in P1 position)
        for add_obs in self.RLTrajDictP2["add_obs"]:
            add_obs.pop("P1")
            add_obs["P1"] = add_obs.pop("P2")
            add_obs["stage"] = 0

        # Remove P2 info from P1 Observation
        for add_obs in self.RLTrajDict["add_obs"]:
            add_obs.pop("P2")
            add_obs["stage"] = 0
