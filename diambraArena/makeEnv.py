import os
from diambraArena.diambraGym import make_gym_env
from diambraArena.wrappers.diambraWrappers import env_wrapping


def env_settings_check(env_settings):

    # Default parameters
    max_char_to_select = 3

    defaultenv_settings = {}
    defaultenv_settings["game_id"] = "doapp"
    defaultenv_settings["player"] = "Random"
    defaultenv_settings["continueGame"] = 0.0
    defaultenv_settings["showFinal"] = True
    defaultenv_settings["stepRatio"] = 6
    defaultenv_settings["difficulty"] = 3
    defaultenv_settings["characters"] = [
        ["Random" for ichar in range(max_char_to_select)] for iplayer in range(2)]
    defaultenv_settings["charOutfits"] = [2, 2]
    defaultenv_settings["frameShape"] = [0, 0, 0]
    defaultenv_settings["actionSpace"] = "multiDiscrete"
    defaultenv_settings["attackButCombination"] = True

    # SFIII Specific
    defaultenv_settings["superArt"] = [0, 0]

    # UMK3 Specific
    defaultenv_settings["tower"] = 3

    # KOF Specific
    defaultenv_settings["fightingStyle"] = [0, 0]
    defaultenv_settings["ultimateStyle"] = [[0, 0, 0], [0, 0, 0]]

    defaultenv_settings["hardCore"] = False
    defaultenv_settings["disableKeyboard"] = True
    defaultenv_settings["disableJoystick"] = True
    defaultenv_settings["rank"] = 0
    defaultenv_settings["recordConfigFile"] = "\"\""

    for k, v in env_settings.items():

        # Check for characters
        if k == "characters":
            for iplayer in range(2):
                for ichar in range(len(v[iplayer]), max_char_to_select):
                    v[iplayer].append("Random")

        defaultenv_settings[k] = v

    if defaultenv_settings["player"] != "P1P2":
        defaultenv_settings["actionSpace"] = [defaultenv_settings["actionSpace"],
                                              defaultenv_settings["actionSpace"]]
        defaultenv_settings["attackButCombination"] = [defaultenv_settings["attackButCombination"],
                                                       defaultenv_settings["attackButCombination"]]
    else:
        for key in ["actionSpace", "attackButCombination"]:
            if type(defaultenv_settings[key]) != list:
                defaultenv_settings[key] = [defaultenv_settings[key],
                                            defaultenv_settings[key]]

    return defaultenv_settings


def make(game_id, env_settings={}, wrappers_settings={},
         traj_rec_settings=None, seed=42, rank=0):
    """
    Create a wrapped environment.
    :param seed: (int) the initial seed for RNG
    :param wrappers_settings: (dict) the parameters for envWrapping function
    """

    # Include game_id in env_settings
    env_settings["game_id"] = game_id

    # Check if DIAMBRA_ENVS var present
    env_addresses = os.getenv("DIAMBRA_ENVS", "").split()
    if len(env_addresses) >= 1:  # If present
        # Check if there are at least n env_addresses as the prescribed rank
        if len(env_addresses) < rank+1:
            print(
                "ERROR: Rank of env client is higher "
                "than the available env_addresses servers:")
            print("       # of env servers: {}".format(len(env_addresses)))
            print("       # rank of client: {} (0-based index)".format(rank))
            raise Exception("Wrong number of env servers vs clients")
    else:  # If not present, set default value
        if "envAddress" not in env_settings:
            env_addresses = ["localhost:50051"]
        else:
            env_addresses = [env_settings["envAddress"]]

    env_settings["envAddress"] = env_addresses[rank]
    env_settings["rank"] = rank

    # Checking settings and setting up default ones
    env_settings = env_settings_check(env_settings)

    # Initialize random seed
    env, player = make_gym_env(env_settings)

    # Initialize random seed
    env.seed(seed)

    # Apply environment wrappers
    env = env_wrapping(env, player, **wrappers_settings,
                       hard_core=env_settings["hardCore"])

    # Apply trajectories recorder wrappers
    if traj_rec_settings is not None:
        if env_settings["hardCore"]:
            from diambraArena.wrappers.trajRecWrapperHardCore import TrajectoryRecorder
        else:
            from diambraArena.wrappers.trajRecWrapper import TrajectoryRecorder

        env = TrajectoryRecorder(env, **traj_rec_settings)

    return env
