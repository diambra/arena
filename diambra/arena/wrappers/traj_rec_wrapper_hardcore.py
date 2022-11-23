import os
import numpy as np
import datetime

import gym
from ..utils.gym_utils import ParallelPickleWriter
from diambra.arena.env_settings import RecordingSettings

# Trajectory recorder wrapper
class TrajectoryRecorder(gym.Wrapper):
    def __init__(self, env, recording_settings: RecordingSettings):
        """
        Record trajectories to use them for imitation learning
        :param env: (Gym Environment) the environment to wrap
        """
        gym.Wrapper.__init__(self, env)
        self.file_path = recording_settings.file_path
        self.username = recording_settings.username
        self.ignore_p2 = recording_settings.ignore_p2
        self.frame_shp = self.env.observation_space.shape

        if (self.env.player_side == "P1P2"):
            if ((self.env.attack_but_combination[0] != self.env.attack_but_combination[1])
                    or (self.env.action_space["P1"] != self.env.action_space["P2"])):
                raise Exception("Different attack buttons combinations and/or "
                                "different action spaces not supported for 2P "
                                "experience recordings"
                                "action space: {}, attack button combo: {}".format(self.env.action_space, self.env.attack_but_combination)
                                )

        env.logger.info("Recording trajectories in \"{}\"".format(self.file_path))
        os.makedirs(self.file_path, exist_ok=True)

    def reset(self, **kwargs):
        """
        Reset the environment and add requested info to the observation
        :return: observation
        """

        # Items to store
        self.last_frame_hist = []
        self.rewards_hist = []
        self.actions_hist = []
        self.flag_hist = []
        self.cumulative_rew = 0

        obs = self.env.reset(**kwargs)

        for idx in range(self.frame_shp[2]):
            self.last_frame_hist.append(obs[:, :, idx])

        return obs

    def step(self, action):
        """
        Step the environment with the given action
        and add requested info to the observation
        :param action: ([int] or [float]) the action
        :return: new observation, reward, done, information
        """

        obs, reward, done, info = self.env.step(action)

        self.last_frame_hist.append(obs[:, :, self.frame_shp[2]-1])

        # Add last obs nFrames - 1 times in case of
        # new round / stage / continue_game
        if ((info["round_done"] or info["stage_done"] or info["game_done"]) and not done):
            for _ in range(self.frame_shp[2]-1):
                self.last_frame_hist.append(obs[:, :, self.frame_shp[2]-1])

        self.rewards_hist.append(reward)
        self.actions_hist.append(action)
        self.flag_hist.append([info["round_done"], info["stage_done"],
                              info["game_done"], info["ep_done"]])
        self.cumulative_rew += reward

        if done:
            to_save = {}
            n_actions = self.env.n_actions if self.env.player_side != "P1P2" else self.env.n_actions[0]
            to_save["username"] = self.username
            to_save["player_side"] = self.env.player_side
            if self.env.player_side != "P1P2":
                to_save["difficulty"] = self.env.difficulty
                if isinstance(self.env.action_space, gym.spaces.Discrete):
                    to_save["action_space"] = "discrete"
                else:
                    to_save["action_space"] = "multi_discrete"
                to_save["attack_but_comb"] = self.env.attack_but_combination
            else:
                if isinstance(self.env.action_space["P1"], gym.spaces.Discrete):
                    to_save["action_space"] = "discrete"
                else:
                    to_save["action_space"] = "multi_discrete"
                to_save["attack_but_comb"] = self.env.attack_but_combination[0]
            to_save["n_actions"] = n_actions
            to_save["frame_shp"] = self.frame_shp
            to_save["ignore_p2"] = self.ignore_p2
            to_save["char_names"] = self.env.char_names
            to_save["n_actions_stack"] = 0
            to_save["ep_len"] = len(self.rewards_hist)
            to_save["cum_rew"] = self.cumulative_rew
            to_save["frames"] = self.last_frame_hist
            to_save["rewards"] = self.rewards_hist
            to_save["actions"] = self.actions_hist
            to_save["done_flags"] = self.flag_hist
            to_save["obs_space_bounds"] = [self.env.observation_space.low[0][0][0],
                                           self.env.observation_space.high[0][0][0]]

            # Characters name
            # If 2P mode
            if self.env.player_side == "P1P2" and self.ignore_p2 == 0:
                save_path = "HC_mod" + str(self.ignore_p2) + "_" +\
                           self.env.player_side + "_rew" +\
                           str(np.round(self.cumulative_rew, 3)) + "_" +\
                           datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            # If 1P mode
            else:
                save_path = "HC_mod" + str(self.ignore_p2) + "_" +\
                           self.env.player_side + "_diff" +\
                           str(self.env.difficulty) + "_rew" +\
                           str(np.round(self.cumulative_rew, 3)) + "_" +\
                           datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            pickle_writer = ParallelPickleWriter(
                os.path.join(self.file_path, save_path), to_save)
            pickle_writer.start()

        return obs, reward, done, info
