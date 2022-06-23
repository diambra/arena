import os
from .arena_gym import make_gym_env
from .wrappers.arena_wrappers import env_wrapping


def env_settings_check(env_settings):

    # Default parameters
    max_char_to_select = 3

    defaultenv_settings = {}
    defaultenv_settings["game_id"] = "doapp"
    defaultenv_settings["player"] = "Random"
    defaultenv_settings["continue_game"] = 0.0
    defaultenv_settings["show_final"] = True
    defaultenv_settings["step_ratio"] = 6
    defaultenv_settings["difficulty"] = 3
    defaultenv_settings["characters"] = [
        ["Random" for ichar in range(max_char_to_select)] for iplayer in range(2)]
    defaultenv_settings["char_outfits"] = [2, 2]
    defaultenv_settings["frame_shape"] = [0, 0, 0]
    defaultenv_settings["action_space"] = "multi_discrete"
    defaultenv_settings["attack_but_combination"] = True

    # SFIII Specific
    defaultenv_settings["super_art"] = [0, 0]

    # UMK3 Specific
    defaultenv_settings["tower"] = 3

    # KOF Specific
    defaultenv_settings["fighting_style"] = [0, 0]
    defaultenv_settings["ultimate_style"] = [[0, 0, 0], [0, 0, 0]]

    defaultenv_settings["hard_core"] = False
    defaultenv_settings["disable_keyboard"] = True
    defaultenv_settings["disable_joystick"] = True
    defaultenv_settings["rank"] = 0
    defaultenv_settings["record_config_file"] = "\"\""

    for k, v in env_settings.items():

        # Check for characters
        if k == "characters":
            for iplayer in range(2):
                for ichar in range(len(v[iplayer]), max_char_to_select):
                    v[iplayer].append("Random")

        defaultenv_settings[k] = v

    if defaultenv_settings["player"] != "P1P2":
        defaultenv_settings["action_space"] = [defaultenv_settings["action_space"],
                                               defaultenv_settings["action_space"]]
        defaultenv_settings["attack_but_combination"] = [defaultenv_settings["attack_but_combination"],
                                                         defaultenv_settings["attack_but_combination"]]
    else:
        for key in ["action_space", "attack_but_combination"]:
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
        if "env_address" not in env_settings:
            env_addresses = ["localhost:50051"]
        else:
            env_addresses = [env_settings["env_address"]]

    env_settings["env_address"] = env_addresses[rank]
    env_settings["rank"] = rank

    # Checking settings and setting up default ones
    env_settings = env_settings_check(env_settings)

    # Initialize random seed
    env, player = make_gym_env(env_settings)

    # Initialize random seed
    env.seed(seed)

    # Apply environment wrappers
    env = env_wrapping(env, player, **wrappers_settings,
                       hard_core=env_settings["hard_core"])

    # Apply trajectories recorder wrappers
    if traj_rec_settings is not None:
        if env_settings["hard_core"]:
            from diambra.arena.wrappers.traj_rec_wrapper_hard_core import TrajectoryRecorder
        else:
            from diambra.arena.wrappers.traj_rec_wrapper import TrajectoryRecorder

        env = TrajectoryRecorder(env, **traj_rec_settings)

    return env
