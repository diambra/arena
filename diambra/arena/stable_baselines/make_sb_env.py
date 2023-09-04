import os
import diambra.arena
import gym

from stable_baselines import logger
from stable_baselines.bench import Monitor
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv

def make_sb_env(env_settings: dict, wrappers_settings: dict={}, episode_recording_settings: dict={},
                render_mode: str="rgb_array", start_index: int=0, allow_early_resets: bool=True,
                start_method: str=None, no_vec: bool=False, use_subprocess: bool=False):
    """
    Create a wrapped, monitored VecEnv.
    :param env_settings: (dict) parameters for DIAMBRA environment
    :param wrappers_settings: (dict) parameters for environment wrapping function
    :param episode_recording_settings: (dict) parameters for environment recording wrapping function
    :param start_index: (int) start rank index
    :param allow_early_resets: (bool) allows early reset of the environment
    :param start_method: (str) method used to start the subprocesses. See SubprocVecEnv doc for more information
    :param use_subprocess: (bool) Whether to use `SubprocVecEnv` or `DummyVecEnv` when
    :param no_vec: (bool) Whether to avoid usage of Vectorized Env or not. Default: False
    :return: (VecEnv) The diambra environment
    """

    env_addresses = os.getenv("DIAMBRA_ENVS", "").split()
    if len(env_addresses) == 0:
        print("WARNING: running script without diambra CLI, this is a development option only.")
        env_addresses = ["0.0.0.0:50051"]

    num_envs = len(env_addresses)

    # Add the conversion from gymnasium to gym
    old_gym_wrapper = [OldGymWrapper, {}]
    if 'additional_wrappers_list' in wrappers_settings:
        wrappers_settings['additional_wrappers_list'].insert(0, old_gym_wrapper)
    else:
        # If it's not present, add the key with a new list containing your custom element
        wrappers_settings['additional_wrappers_list'] = [old_gym_wrapper]

    def _make_sb_env(rank):
        def _thunk():
            env = diambra.arena.make(env_settings["game_id"], env_settings, wrappers_settings,
                                     episode_recording_settings, render_mode, rank=rank)

            env = Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)),
                          allow_early_resets=allow_early_resets)
            return env
        return _thunk

    # If not wanting vectorized envs
    if no_vec and num_envs == 1:
        return _make_sb_env(0)(), num_envs

    # When using one environment, no need to start subprocesses
    if num_envs == 1 or not use_subprocess:
        return DummyVecEnv([_make_sb_env(i + start_index) for i in range(num_envs)]), num_envs

    return SubprocVecEnv([_make_sb_env(i + start_index) for i in range(num_envs)], start_method=start_method), num_envs

class OldGymWrapper(gym.Wrapper):
    def __init__(self, env):
        """
        Convert gymnasium to gym<=0.21 environment
        :param env: (Gymnasium Environment) the environment to wrap
        :param env: (Gym<=0.21 Environment) the resulting environment
        """
        gym.Wrapper.__init__(self, env)
        if self.env_settings.action_space == "multi_discrete":
            self.action_space = gym.spaces.MultiDiscrete(self.n_actions)
            self.logger.debug("Using MultiDiscrete action space")
        elif self.env_settings.action_space == "discrete":
            self.action_space = gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
            self.logger.debug("Using Discrete action space")

    def reset(self, **kwargs):
        obs, _ = self.env.reset(**kwargs)
        return obs

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        return obs, reward, terminated or truncated, info