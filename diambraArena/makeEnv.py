from diambraArena.diambraGym import *
from diambraArena.wrappers.diambraWrappers import *

def makeEnv(envPrefix, seed, diambraKwargs, diambraGymKwargs,
            wrapperKwargs=None, trajRecKwargs=None, hardCore=False):
    """
    Create a wrapped environment.
    :param seed: (int) the initial seed for RNG
    :param wrapperKwargs: (dict) the parameters for envWrapping function
    """

    if diambraKwargs["player"] != "P1P2": #1P Mode
        if hardCore:
            env = diambraGymHardCore1P(envPrefix, diambraKwargs, **diambraGymKwargs)
        else:
            env = diambraGym1P(envPrefix, diambraKwargs, **diambraGymKwargs)
    else: #2P Mode
        if hardCore:
            env = diambraGymHardCore2P(envPrefix, diambraKwargs, **diambraGymKwargs)
        else:
            env = diambraGym2P(envPrefix, diambraKwargs, **diambraGymKwargs)

    env.seed(seed)

    if wrapperKwargs is not None:
        env = envWrapping(env, diambraKwargs["player"], **wrapperKwargs, hardCore=hardCore)

    if trajRecKwargs is not None:
        if hardCore:
            from diambraArena.wrappers.trajRecWrapperHardCore import TrajectoryRecorder
        else:
            from diambraArena.wrappers.trajRecWrapper import TrajectoryRecorder

        env = TrajectoryRecorder(env, **trajRecKwargs)

    return env
