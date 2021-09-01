from diambraArena.diambraGym import makeGymEnv
from diambraArena.wrappers.diambraWrappers import envWrapping

def make(envPrefix, diambraKwargs, diambraGymKwargs={},
         wrapperKwargs={}, trajRecKwargs=None, seed=42, hardCore=False):
    """
    Create a wrapped environment.
    :param seed: (int) the initial seed for RNG
    :param wrapperKwargs: (dict) the parameters for envWrapping function
    """

    # Initialize random seed
    env, player = makeGymEnv(envPrefix, diambraKwargs, diambraGymKwargs, hardCore)

    # Initialize random seed
    env.seed(seed)

    # Apply environment wrappers
    env = envWrapping(env, player, **wrapperKwargs, hardCore=hardCore)

    # Apply trajectories recorder wrappers
    if trajRecKwargs is not None:
        if hardCore:
            from diambraArena.wrappers.trajRecWrapperHardCore import TrajectoryRecorder
        else:
            from diambraArena.wrappers.trajRecWrapper import TrajectoryRecorder

        env = TrajectoryRecorder(env, **trajRecKwargs)

    return env
