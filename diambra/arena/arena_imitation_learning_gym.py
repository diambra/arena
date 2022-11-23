import numpy as np
import gym
from gym import spaces
import pickle
import bz2
import copy
import cv2
import sys
import os
import logging
from .utils.splash_screen import SplashScreen
from .utils.gym_utils import standard_dict_to_gym_obs_dict,\
    discrete_to_multi_discrete_action
from typing import List

# Diambra imitation learning environment


class ImitationLearningBase(gym.Env):
    """Diambra Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, traj_files_list: List[str], rank: int=0, total_cpus: int=1):
        self.logger = logging.getLogger(__name__)
        super(ImitationLearningBase, self).__init__()

        # Check for number of files
        if total_cpus > len(traj_files_list):
            raise Exception(
                "Number of requested CPUs > number of "
                "recorded experience available files")

        # Splash Screen
        SplashScreen()

        # List of RL trajectories files
        self.traj_files_list = traj_files_list

        # CPU rank for this env instance
        self.rank = rank
        self.total_cpus = total_cpus

        # Idx of trajectory file to read
        self.traj_idx = self.rank
        self.rl_traj_dict = None

        # Open the first file to retrieve env info: ---
        tmp_rl_traj_file = self.traj_files_list[self.traj_idx]

        # Read compressed RL Traj file
        infile = bz2.BZ2File(tmp_rl_traj_file, 'r')
        self.tmp_rl_traj_dict = pickle.load(infile)
        infile.close()

        # Observation and action space
        self.frame_h = self.tmp_rl_traj_dict["frame_shp"][0]
        self.frame_w = self.tmp_rl_traj_dict["frame_shp"][1]
        self.frame_n_channels = self.tmp_rl_traj_dict["frame_shp"][2]
        self.n_actions = self.tmp_rl_traj_dict["n_actions"]
        # ---

        # Define action and observation space
        # They must be gym.spaces objects
        if self.tmp_rl_traj_dict["action_space"] == "multi_discrete":
            # MultiDiscrete actions:
            # - Arrows -> One discrete set
            # - Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.MultiDiscrete(self.n_actions)
            self.logger.debug("Using MultiDiscrete action space")
        elif self.tmp_rl_traj_dict["action_space"] == "discrete":
            # Discrete actions:
            # - Arrows U Buttons -> One discrete set
            # NB: use the convention NOOP = 0, and buttons combinations
            #     can be prescripted:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2], ButA+ButB = [3]
            #     or ignored:
            #     e.g. NOOP = [0], ButA = [1], ButB = [2]
            self.action_space = spaces.Discrete(
                self.n_actions[0] + self.n_actions[1] - 1)
            self.logger.debug("Using Discrete action space")
        else:
            raise Exception(
                "Not recognized action space: {}".format(self.tmp_rl_traj_dict["action_space"]))

        # If run out of examples
        self.exhausted = False

        # Reset flag
        self.n_reset = 0

        # Observations shift counter (for new round/stage/game)
        self.shift_counter = 1

    # Print Episode summary
    def traj_summary(self):

        self.logger.info(self.rl_traj_dict.keys())

        self.logger.info("Ep. length = {}".format(self.rl_traj_dict["ep_len"]))

        for key, value in self.rl_traj_dict.items():
            if type(value) == list and len(value) > 2:
                self.logger.info("len({}): {}".format(key, len(value)))
            else:
                self.logger.info("{} : {}".format(key, value))

    # Step the environment
    def step(self, dummy_action):

        # Done retrieval
        done = False
        if self.step_idx == self.rl_traj_dict["ep_len"] - 1:
            done = True

        # Done flags retrieval
        done_flags = self.rl_traj_dict["done_flags"][self.step_idx]

        if (done_flags[0] or done_flags[1] or done_flags[2]) and not done:
            self.shift_counter += self.frame_n_channels - 1

        # Observation retrieval
        observation = self.obs_retrieval()

        # Reward retrieval
        reward = self.rl_traj_dict["rewards"][self.step_idx]

        # Action retrieval
        action = self.rl_traj_dict["actions"][self.step_idx]
        if isinstance(self.action_space, gym.spaces.Discrete):
            action_new = discrete_to_multi_discrete_action(action, self.n_actions[0])
        else:
            action_new = action

        action = [action_new[0], action_new[1]]
        info = {}
        info["action"] = action
        info["round_done"] = done_flags[0]
        info["stage_done"] = done_flags[1]
        info["game_done"] = done_flags[2]
        info["episode_done"] = done_flags[3]

        if np.any(done):
            self.logger.info("(Rank {}) Episode done".format(self.rank))

        # Update step idx
        self.step_idx += 1

        return observation, reward, done, info

    # Resetting the environment
    def reset(self):

        # Reset run step
        self.step_idx = 0

        # Observations shift counter (for new round/stage/game)
        self.shift_counter = 1

        # Manage ignoreP2 flag for recorded P1P2 trajectory (e.g. when HUMvsAI)
        if self.n_reset != 0 and self.rl_traj_dict["ignore_p2"] == 1:

            self.logger.debug("Skipping P2 trajectory for 2P games (e.g. HUMvsAI)")
            # Resetting n_reset
            self.n_reset = 0
            # Move traj idx to the next to be read
            self.traj_idx += self.total_cpus

        # Check if run out of traj files
        if self.traj_idx >= len(self.traj_files_list):
            self.logger.info("(Rank {}) Resetting env".format(self.rank))
            self.exhausted = True
            observation = {}
            observation = self.black_screen(observation)
            return observation

        if self.n_reset == 0:
            rl_traj_file = self.traj_files_list[self.traj_idx]

            # Read compressed RL Traj file
            infile = bz2.BZ2File(rl_traj_file, 'r')
            self.rl_traj_dict = pickle.load(infile)
            infile.close()

            # Storing env info
            self.n_chars = len(self.rl_traj_dict["char_names"])
            self.char_names = self.rl_traj_dict["char_names"]
            self.n_actions_stack = self.rl_traj_dict["n_actions_stack"]
            self.player_side = self.rl_traj_dict["player_side"]
            assert self.n_actions == self.rl_traj_dict["n_actions"],\
                "Recorded episode has {} actions".format(
                    self.rl_traj_dict["n_actions"])
            if isinstance(self.action_space, gym.spaces.Discrete):
                assert self.rl_traj_dict["action_space"] == "discrete",\
                    "Recorded episode has {} action space".format(
                        self.rl_traj_dict["action_space"])
            else:
                assert self.rl_traj_dict["action_space"] == "multi_discrete",\
                    "Recorded episode has {} action space".format(
                        self.rl_traj_dict["action_space"])

        if self.player_side == "P1P2":

            self.logger.debug("Two players RL trajectory")

            if self.n_reset == 0:
                # First reset for this trajectory

                self.logger.debug("Loading P1 data for 2P trajectory")

                # Generate P2 Experience from P1 one
                self.generate_p2_experience_from_p1()

                # For each step, isolate P1 actions from P1P2 experience
                for idx in range(self.rl_traj_dict["ep_len"]):
                    # Actions (inverting sides)
                    if self.rl_traj_dict["action_space"] == "discrete":
                        self.rl_traj_dict["actions"][idx] = self.rl_traj_dict["actions"][idx][0]
                    else:
                        self.rl_traj_dict["actions"][idx] = [self.rl_traj_dict["actions"][idx][0],
                                                             self.rl_traj_dict["actions"][idx][1]]

                # Update reset counter
                self.n_reset += 1

            else:
                # Second reset for this trajectory

                self.logger.debug("Loading P2 data for 2P trajectory")

                # OverWrite P1 RL trajectory with the one calculated for P2
                self.rl_traj_dict = self.rl_traj_dict_p2

                # Reset reset counter
                self.n_reset = 0

                # Move traj idx to the next to be read
                self.traj_idx += self.total_cpus

        else:

            self.logger.debug("One player RL trajectory")

            # Move traj idx to the next to be read
            self.traj_idx += self.total_cpus

        # Observation retrieval
        observation = self.obs_retrieval(reset_shift=1)

        return observation

    # Generate P2 Experience from P1 one
    def generate_p2_experience_from_p1(self):

        # Copy P1 Trajectory
        self.rl_traj_dict_p2 = copy.deepcopy(self.rl_traj_dict)

        # For each step, convert P1 into P2 experience
        for idx in range(self.rl_traj_dict["ep_len"]):

            # Rewards (inverting sign)
            self.rl_traj_dict_p2["rewards"][idx] = - \
                self.rl_traj_dict["rewards"][idx]

            # Actions (inverting sides)
            if self.rl_traj_dict["action_space"] == "discrete":
                self.rl_traj_dict_p2["actions"][idx] = self.rl_traj_dict["actions"][idx][1]
            else:
                self.rl_traj_dict_p2["actions"][idx] = [self.rl_traj_dict["actions"][idx][2],
                                                        self.rl_traj_dict["actions"][idx][3]]

    # Rendering the environment
    def render(self, mode='human'):

        if mode == "human":
            window_name = "Diambra Imitation Learning Environment - {}".format(
                self.rank)
            cv2.namedWindow(window_name, cv2.WINDOW_GUI_NORMAL)
            cv2.imshow(window_name, self.last_obs)
            cv2.waitKey(1)
        elif mode == "rgb_array":
            output = np.expand_dims(self.last_obs, axis=2)
            return output

    # Print observation details to the console
    def show_obs(self, observation, wait_key=1, viz=True):

        if type(observation) == dict:
            for k, v in observation.items():
                if k != "frame":
                    if type(v) == dict:
                        for k2, v2 in v.items():
                            if k2 == "actions":

                                for k3, v3 in v2.items():
                                    out_value = v3
                                    additional_string = ": "
                                    if type(v3) != int:
                                        n_actions_stack = int(self.observation_space[k][k2][k3].n / (self.n_actions[0] if k3 == "move" else self.n_actions[1]))
                                        out_value = np.reshape(v3, [n_actions_stack, -1])
                                        additional_string = " (reshaped for visualization):\n"
                                    print("observation[\"{}\"][\"{}\"][\"{}\"]{}{}".format(k, k2, k3, additional_string, out_value))
                            elif "ownChar" in k2 or "oppChar" in k2:
                                char_idx = v2 if type(v2) == int else np.where(v2 == 1)[0][0]
                                print("observation[\"{}\"][\"{}\"]: {} / {}".format(k, k2, v2, self.char_names[char_idx]))
                            else:
                                print("observation[\"{}\"][\"{}\"]: {}".format(k, k2, v2))
                    else:
                        print("observation[\"{}\"]: {}".format(k, v))
                else:
                    frame = observation["frame"]
                    print("observation[\"frame\"]: shape {} - min {} - max {}".format(frame.shape, np.amin(frame), np.amax(frame)))

            if viz:
                frame = observation["frame"]
        else:
            if viz:
                frame = observation

        if viz is True and (sys.platform.startswith('linux') is False or 'DISPLAY' in os.environ):
            try:
                norm_factor = 255 if np.amax(frame) > 1.0 else 1.0
                for idx in range(frame.shape[2]):
                    cv2.imshow("[{}] Frame channel {}".format(os.getpid(), idx), frame[:, :, idx] / norm_factor)

                cv2.waitKey(wait_key)
            except:
                pass

# Diambra imitation learning environment
class ImitationLearningHardcore(ImitationLearningBase):
    def __init__(self, traj_files_list: List[str], rank: int=0, total_cpus: int=1):
        super().__init__(traj_files_list, rank, total_cpus)

        # Observation space
        obs_space_bounds = self.tmp_rl_traj_dict["obs_space_bounds"]

        # Create the observation space
        self.observation_space = spaces.Box(low=obs_space_bounds[0],
                                            high=obs_space_bounds[1],
                                            shape=(self.frame_h, self.frame_w,
                                                   self.frame_n_channels),
                                            dtype=np.float32)

    # Specific observation retrieval
    def obs_retrieval(self, reset_shift=0):
        # Observation retrieval
        observation = np.zeros((self.frame_h, self.frame_w, self.frame_n_channels))
        for iframe in range(self.frame_n_channels):
            observation[:, :, iframe] = self.rl_traj_dict["frames"][self.step_idx +
                                                                    self.shift_counter + iframe - reset_shift]
        # Storing last observation for rendering
        self.last_obs = observation[:, :, self.frame_n_channels - 1]

        return observation

    # Black screen
    def black_screen(self, observation):

        observation = np.zeros((self.frame_h, self.frame_w, self.frame_n_channels))

        return observation

# Diambra imitation learning environment
class ImitationLearning(ImitationLearningBase):
    def __init__(self, traj_files_list: List[str], rank: int=0, total_cpus: int=1):
        super().__init__(traj_files_list, rank, total_cpus)

        # Observation space
        player_side = self.tmp_rl_traj_dict["player_side"]
        self.observation_space_dict = self.tmp_rl_traj_dict["observation_space_dict"]
        # Remove P2 sub space from Obs Space
        if player_side == "P1P2":
            self.observation_space_dict.pop("P2")

        # Create the observation space
        self.observation_space = standard_dict_to_gym_obs_dict(
            self.observation_space_dict)

    # Specific observation retrieval
    def obs_retrieval(self, reset_shift=0):
        # Observation retrieval
        observation = self.rl_traj_dict["ram_states"][self.step_idx + 1 - reset_shift].copy()

        # Frame
        observation["frame"] = np.zeros(
            (self.frame_h, self.frame_w, self.frame_n_channels))
        for iframe in range(self.frame_n_channels):
            observation["frame"][:, :, iframe] = self.rl_traj_dict["frames"][self.step_idx +
                                                                             self.shift_counter + iframe - reset_shift]
        # Storing last observation for rendering
        self.last_obs = observation["frame"][:, :, self.frame_n_channels - 1]

        return observation

    # Black screen
    def black_screen(self, observation):

        observation["frame"] = np.zeros(
            (self.frame_h, self.frame_w, self.frame_n_channels))

        return observation

    # Generate P2 Experience from P1 one
    def generate_p2_experience_from_p1(self):

        super().generate_p2_experience_from_p1()

        # Process Additiona Obs for P2 (copy them in P1 position)
        for ram_states in self.rl_traj_dict_p2["ram_states"]:
            ram_states.pop("P1")
            ram_states["P1"] = ram_states.pop("P2")
            ram_states["stage"] = 0

        # Remove P2 info from P1 Observation
        for ram_states in self.rl_traj_dict["ram_states"]:
            ram_states.pop("P2")
            ram_states["stage"] = 0
