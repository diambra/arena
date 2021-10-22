from diambraArena.diambraGym import makeGymEnv
from diambraArena.wrappers.diambraWrappers import envWrapping

def make(envPrefix, diambraKwargs, wrapperKwargs={}, trajRecKwargs=None,
         seed=42):
    """
    Create a wrapped environment.
    :param seed: (int) the initial seed for RNG
    :param wrapperKwargs: (dict) the parameters for envWrapping function
    """

    diambraGymKwargs={}
    keys = ["rewNormFact", "actionSpace", "attackButCombination"]
    for key in keys:
        if key in diambraKwargs:
            diambraGymKwargs[key] = diambraKwargs[key]

    hardCore=False
    if "hardCore" in diambraKwargs:
        hardCore = diambraKwargs["hardCore"]

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
