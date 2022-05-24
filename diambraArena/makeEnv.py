import os
from diambraArena.diambraGym import makeGymEnv
from diambraArena.wrappers.diambraWrappers import envWrapping

def envSettingsCheck(envSettings):

    # Default parameters
    maxCharToSelect = 3

    defaultEnvSettings = {}
    defaultEnvSettings["gameId"] = "doapp"
    defaultEnvSettings["player"] = "Random"
    defaultEnvSettings["continueGame"] = 0.0
    defaultEnvSettings["showFinal"] = True
    defaultEnvSettings["stepRatio"] = 6
    defaultEnvSettings["difficulty"] = 3
    defaultEnvSettings["characters"] = [["Random" for iChar in range(maxCharToSelect)] for iPlayer in range(2)]
    defaultEnvSettings["charOutfits"] = [2, 2]
    defaultEnvSettings["actionSpace"] = "multiDiscrete"
    defaultEnvSettings["attackButCombination"] = True

    # SFIII Specific
    defaultEnvSettings["superArt"] = [0, 0]

    # UMK3 Specific
    defaultEnvSettings["tower"] = 3

    # KOF Specific
    defaultEnvSettings["fightingStyle"] = [0, 0]
    defaultEnvSettings["ultimateStyle"] = [[0, 0, 0], [0, 0, 0]]

    defaultEnvSettings["hardCore"] = False
    defaultEnvSettings["disableKeyboard"] = True
    defaultEnvSettings["disableJoystick"] = True
    defaultEnvSettings["rank"] = 0
    defaultEnvSettings["recordConfigFile"] = ""

    for k, v in envSettings.items():

        # Check for characters
        if k == "characters":
            for iPlayer in range(2):
                for iChar in range(len(v[iPlayer]), maxCharToSelect):
                    v[iPlayer].append("Random")

        defaultEnvSettings[k] = v

    if defaultEnvSettings["player"] != "P1P2":
        defaultEnvSettings["actionSpace"] = [defaultEnvSettings["actionSpace"],
                                             defaultEnvSettings["actionSpace"]]
        defaultEnvSettings["attackButCombination"] = [defaultEnvSettings["attackButCombination"],
                                                      defaultEnvSettings["attackButCombination"]]
    else:
        for key in ["actionSpace", "attackButCombination"]:
            if type(defaultEnvSettings[key]) != list:
                defaultEnvSettings[key] = [defaultEnvSettings[key],
                                           defaultEnvSettings[key]]

    # Check if DIAMBRA_ENVS var present
    envs = os.getenv("DIAMBRA_ENVS", "").split()
    if len(envs) >= 1: # If present
        # Check if there are at least n envs as the prescribed rank
        if len(envs) < defaultEnvSettings["rank"]+1:
            print("ERROR: Rank of env client is higher than the available envs servers:")
            print("       # of env servers: {}".format(len(envs)))
            print("       # rank of client: {} (0-based index)".format(defaultEnvSettings["rank"]))
            raise Exception("Wrong number of env servers vs clients")
    else: # If not present, set default value
        if "envAddress" not in defaultEnvSettings:
            envs = ["localhost:50051"]
        else:
            envs = [defaultEnvSettings["envAddress"]]

    defaultEnvSettings["envAddress"] = envs[defaultEnvSettings["rank"]]

    return defaultEnvSettings


def make(gameId, envSettings={}, wrappersSettings={}, trajRecSettings=None, seed=42):
    """
    Create a wrapped environment.
    :param seed: (int) the initial seed for RNG
    :param wrappersSettings: (dict) the parameters for envWrapping function
    """

    # Include gameId in envSettings
    envSettings["gameId"] = gameId

    # Checking settings and setting up default ones
    envSettings = envSettingsCheck(envSettings)

    # Initialize random seed
    env, player = makeGymEnv(envSettings)

    # Initialize random seed
    env.seed(seed)

    # Apply environment wrappers
    env = envWrapping(env, player, **wrappersSettings, hardCore=envSettings["hardCore"])

    # Apply trajectories recorder wrappers
    if trajRecSettings is not None:
        if envSettings["hardCore"]:
            from diambraArena.wrappers.trajRecWrapperHardCore import TrajectoryRecorder
        else:
            from diambraArena.wrappers.trajRecWrapper import TrajectoryRecorder

        env = TrajectoryRecorder(env, **trajRecSettings)

    return env
