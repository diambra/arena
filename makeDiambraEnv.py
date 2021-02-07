from diambraWrappers import *

def make_diambra_env(diambraGym, env_prefix, seed, diambra_kwargs, diambra_gym_kwargs,
                     wrapper_kwargs=None, key_to_add=None):
    """
    Create a wrapped, monitored VecEnv for Atari.
    :param diambraGym: (class) DIAMBRAGym interface class
    :param seed: (int) the initial seed for RNG
    :param wrapper_kwargs: (dict) the parameters for wrap_deepmind function
    """
    if wrapper_kwargs is None:
        wrapper_kwargs = {}

    env = make_diambra(diambraGym, env_prefix, diambra_kwargs, diambra_gym_kwargs)
    env.seed(seed)
    env = wrap_deepmind(env, **wrapper_kwargs)
    env = additional_obs(env, key_to_add)

    return env
