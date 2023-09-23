import os
import time
import diambra.arena
from diambra.arena import SpaceTypes, EnvironmentSettings, WrappersSettings, RecordingSettings
import gym

from stable_baselines import logger
from stable_baselines.bench import Monitor
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines.common import set_global_seeds

# Make Stable Baselines Env function
def make_sb_env(game_id: str, env_settings: EnvironmentSettings=EnvironmentSettings(),
                wrappers_settings: WrappersSettings=WrappersSettings(),
                episode_recording_settings: RecordingSettings=RecordingSettings(),
                render_mode: str="rgb_array", seed: int=None, start_index: int=0,
                allow_early_resets: bool=True, start_method: str=None,
                no_vec: bool=False, use_subprocess: bool=False):
    """
    Create a wrapped, monitored VecEnv.
    :param game_id: (str) the game environment ID
    :param env_settings: (dict) parameters for DIAMBRA Arena environment
    :param wrappers_settings: (dict) parameters for environment wrapping function
    :param episode_recording_settings: (dict) parameters for environment recording wrapping function
    :param start_index: (int) start rank index
    :param allow_early_resets: (bool) allows early reset of the environment
    :param start_method: (str) method used to start the subprocesses. See SubprocVecEnv doc for more information
    :param use_subprocess: (bool) Whether to use `SubprocVecEnv` or `DummyVecEnv`
    :param no_vec: (bool) Whether to avoid usage of Vectorized Env or not. Default: False
    :return: (VecEnv) The diambra environment
    """

    env_addresses = os.getenv("DIAMBRA_ENVS", "").split()
    if len(env_addresses) == 0:
        raise Exception("ERROR: Running script without DIAMBRA CLI.")

    num_envs = len(env_addresses)

    # Seed management
    if seed is None:
        seed = int(time.time())
    env_settings.seed = seed

    # Add the conversion from gymnasium to gym
    old_gym_wrapper = [OldGymWrapper, {}]
    wrappers_settings.wrappers.insert(0, old_gym_wrapper)

    def _make_sb_env(rank):
        def _init():
            env = diambra.arena.make(game_id, env_settings, wrappers_settings,
                                     episode_recording_settings, render_mode, rank=rank)

            env = Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)),
                          allow_early_resets=allow_early_resets)
            return env
        set_global_seeds(seed)
        return _init

    # If not wanting vectorized envs
    if no_vec and num_envs == 1:
        env = _make_sb_env(0)()
    else:
        # When using one environment, no need to start subprocesses
        if num_envs == 1 or not use_subprocess:
            env = DummyVecEnv([_make_sb_env(i + start_index) for i in range(num_envs)])
        else:
            env = SubprocVecEnv([_make_sb_env(i + start_index) for i in range(num_envs)],
                                start_method=start_method)

    return env, num_envs

class OldGymWrapper(gym.Wrapper):
    def __init__(self, env):
        """
        Convert gymnasium to gym<=0.21 environment
        :param env: (Gymnasium Environment) the environment to wrap
        :param env: (Gym<=0.21 Environment) the resulting environment
        """
        gym.Wrapper.__init__(self, env)
        if self.env_settings.action_space == SpaceTypes.MULTI_DISCRETE:
            self.action_space = gym.spaces.MultiDiscrete(self.n_actions)
        elif self.env_settings.action_space == SpaceTypes.DISCRETE:
            self.action_space = gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
        self.logger.debug("Using {} action space".format(SpaceTypes.Name(self.env_settings.action_space)))


    def reset(self, **kwargs):
        obs, _ = self.env.reset(**kwargs)
        return obs

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        return obs, reward, terminated or truncated, info
