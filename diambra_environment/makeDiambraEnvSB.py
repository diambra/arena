from diambra_environment.diambraGym import diambraGym
from diambra_environment.diambraWrappers import *

from stable_baselines import logger
from stable_baselines.bench import Monitor
from stable_baselines.common.misc_util import set_global_seeds
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv, VecFrameStack

def make_diambra_env(diambraGym, env_prefix, num_env, seed, diambra_kwargs,
                     diambra_gym_kwargs, wrapper_kwargs=None,
                     start_index=0, allow_early_resets=True, start_method=None,
                     key_to_add=None, no_vec=False, use_subprocess=False):
    """
    Create a wrapped, monitored VecEnv for Atari.
    :param diambraGym: (class) DIAMBRAGym interface class
    :param num_env: (int) the number of environment you wish to have in subprocesses
    :param seed: (int) the initial seed for RNG
    :param wrapper_kwargs: (dict) the parameters for wrap_deepmind function
    :param start_index: (int) start rank index
    :param allow_early_resets: (bool) allows early reset of the environment
    :param start_method: (str) method used to start the subprocesses.
        See SubprocVecEnv doc for more information
    :param use_subprocess: (bool) Whether to use `SubprocVecEnv` or `DummyVecEnv` when
    :param no_vec: (bool) Whether to avoid usage of Vectorized Env or not. Default: False
    :return: (VecEnv) The diambra environment
    """
    if wrapper_kwargs is None:
        wrapper_kwargs = {}

    def make_env(rank):
        def _thunk():
            env_id = env_prefix + str(rank)
            env = make_diambra(diambraGym, env_id, diambra_kwargs, diambra_gym_kwargs)
            env.seed(seed + rank)
            env = wrap_deepmind(env, **wrapper_kwargs)
            env = additional_obs(env, key_to_add)
            env = Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)),
                          allow_early_resets=allow_early_resets)
            return env
        return _thunk
    set_global_seeds(seed)

    # If not wanting vectorized envs
    if no_vec and num_env == 1:
        env_id = env_prefix + str(0)
        env = make_diambra(diambraGym, env_id, diambra_kwargs, diambra_gym_kwargs)
        env.seed(seed)
        env = wrap_deepmind(env, **wrapper_kwargs)
        env = additional_obs(env, key_to_add)
        env = Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)),
                      allow_early_resets=allow_early_resets)
        return env

    # When using one environment, no need to start subprocesses
    if num_env == 1 or not use_subprocess:
        return DummyVecEnv([make_env(i + start_index) for i in range(num_env)])

    return SubprocVecEnv([make_env(i + start_index) for i in range(num_env)],
                         start_method=start_method)
