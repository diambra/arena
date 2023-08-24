import os
import numpy as np
import datetime
import gymnasium as gym
from diambra.arena.utils.gym_utils import ParallelPickleWriter
from diambra.arena.env_settings import RecordingSettings
import copy
import cv2


# Trajectory recorder wrapper
class EpisodeRecorder(gym.Wrapper):
    def __init__(self, env, recording_settings: RecordingSettings):
        """
        Record trajectories to use them for imitation learning
        :param env: (Gym Environment) the environment to wrap
        :param file_path: (str) file path specifying where to
               store the trajectory file
        """
        gym.Wrapper.__init__(self, env)
        self.dataset_path = recording_settings.dataset_path
        self.username = recording_settings.username

        self.compression_parameters = [int(cv2.IMWRITE_JPEG_QUALITY), 80]

        self.env.logger.info("Recording trajectories in \"{}\"".format(self.dataset_path))
        os.makedirs(self.dataset_path, exist_ok=True)

    def reset(self, **kwargs):
        """
        Reset the environment and add requested info to the observation
        :return: observation
        """
        self.episode_data = []

        obs, info = self.env.reset(**kwargs)
        self._last_obs = copy.deepcopy(obs)
        _, self._last_obs["frame"] = cv2.imencode('.jpg', obs["frame"], self.compression_parameters)

        return obs, info

    def step(self, action):
        """
        Step the environment with the given action
        and add requested info to the observation
        :param action: ([int] or [float]) the action
        :return: new observation, reward, done, information
        """
        obs, reward, terminated, truncated, info = self.env.step(action)

        self.episode_data.append({
            "obs": self._last_obs,
            "action": action,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "info": info})
        self._last_obs = copy.deepcopy(obs)
        _, self._last_obs["frame"] = cv2.imencode('.jpg', obs["frame"], self.compression_parameters)

        if terminated or truncated:
            to_save = {}
            to_save["episode_summary"] = {
                "steps": len(self.episode_data),
                "username": self.username,
                "env_settings": self.env.env_settings.pb_model,
            }
            to_save["data"] = self.episode_data

            # Save recording file
            save_path = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + ".diambra"
            pickle_writer = ParallelPickleWriter(os.path.join(self.dataset_path, save_path), to_save)
            pickle_writer.start()

        return obs, reward, terminated, truncated, info
