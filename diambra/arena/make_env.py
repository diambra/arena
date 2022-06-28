import os
from .arena_gym import make_gym_env
from .wrappers.arena_wrappers import env_wrapping


def env_settings_check(env_settings):

    # Default parameters
    max_char_to_select = 3

    default_env_settings = {}
    default_env_settings["game_id"] = "doapp"
    default_env_settings["player"] = "Random"
    default_env_settings["continue_game"] = 0.0
    default_env_settings["show_final"] = True
    default_env_settings["step_ratio"] = 6
    default_env_settings["difficulty"] = 3
    default_env_settings["characters"] = [
        ["Random" for ichar in range(max_char_to_select)] for iplayer in range(2)]
    default_env_settings["char_outfits"] = [2, 2]
    default_env_settings["frame_shape"] = [0, 0, 0]
    default_env_settings["action_space"] = "multi_discrete"
    default_env_settings["attack_but_combination"] = True

    # SFIII Specific
    default_env_settings["super_art"] = [0, 0]

    # UMK3 Specific
    default_env_settings["tower"] = 3

    # KOF Specific
    default_env_settings["fighting_style"] = [0, 0]
    default_env_settings["ultimate_style"] = [[0, 0, 0], [0, 0, 0]]

    default_env_settings["hardcore"] = False
    default_env_settings["disable_keyboard"] = True
    default_env_settings["disable_joystick"] = True
    default_env_settings["rank"] = 0
    default_env_settings["record_config_file"] = "\"\""

    for k, v in env_settings.items():

        # Check for characters
        if k == "characters":
            for iplayer in range(2):
                for ichar in range(len(v[iplayer]), max_char_to_select):
                    v[iplayer].append("Random")

        default_env_settings[k] = v

    if default_env_settings["player"] != "P1P2":
        default_env_settings["action_space"] = [default_env_settings["action_space"],
                                                default_env_settings["action_space"]]
        default_env_settings["attack_but_combination"] = [default_env_settings["attack_but_combination"],
                                                          default_env_settings["attack_but_combination"]]
    else:
        for key in ["action_space", "attack_but_combination"]:
            if type(default_env_settings[key]) != list:
                default_env_settings[key] = [default_env_settings[key],
                                             default_env_settings[key]]

    return default_env_settings


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

    # Make environment
    env, player = make_gym_env(env_settings)

    # Initialize random seed
    env.seed(seed)

    # Apply environment wrappers
    env = env_wrapping(env, player, **wrappers_settings,
                       hardcore=env_settings["hardcore"])

    # Apply trajectories recorder wrappers
    if traj_rec_settings is not None:
        if env_settings["hardcore"]:
            from diambra.arena.wrappers.traj_rec_wrapper_hardcore import TrajectoryRecorder
        else:
            from diambra.arena.wrappers.traj_rec_wrapper import TrajectoryRecorder

        env = TrajectoryRecorder(env, **traj_rec_settings)

    return env
