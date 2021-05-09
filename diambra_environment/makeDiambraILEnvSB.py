import os

from stable_baselines.bench import Monitor
from stable_baselines.common.misc_util import set_global_seeds
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv

# Function to vectorialize envs
def make_diambra_imitationLearning_env(diambraIL, diambraIL_kwargs, seed=0,
                                       allow_early_resets=True, no_vec=False,
                                       use_subprocess=False):
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
        return _thunk

    set_global_seeds(seed)

    # If not wanting vectorized envs
    if no_vec and num_env == 1:
        # Create log dir
        log_dir = "tmp"+str(rank)+"/"
        os.makedirs(log_dir, exist_ok=True)
        env = diambraIL(**diambraIL_kwargs, rank=rank)
        env = Monitor(env, log_dir, allow_early_resets=allow_early_resets)
        return env

    # When using one environment, no need to start subprocesses
    if num_env == 1 or not use_subprocess:
        return DummyVecEnv([make_env(i) for i in range(num_env)])

    return SubprocVecEnv([make_env(i) for i in range(num_env)])
