import os
import logging
from .arena_gym import DiambraGymHardcore1P, DiambraGym1P, DiambraGymHardcore2P, DiambraGym2P
from .wrappers.arena_wrappers import env_wrapping


def env_settings_check(env_settings, logger):

    # Default parameters
    max_char_to_select = 3

    default_env_settings = {}
    default_env_settings["game_id"] = "doapp"
    default_env_settings["player"] = "Random"
    default_env_settings["continue_game"] = 0.0
    default_env_settings["show_final"] = True
    default_env_settings["step_ratio"] = 6
    default_env_settings["difficulty"] = 3
    default_env_settings["frame_shape"] = (0, 0, 0)

    default_env_settings["characters"] = ("Random" for ichar in range(max_char_to_select))
    default_env_settings["char_outfits"] = 2
    default_env_settings["action_space"] = "multi_discrete"
    default_env_settings["attack_but_combination"] = True

    # SFIII Specific
    default_env_settings["super_art"] = 0

    # UMK3 Specific
    default_env_settings["tower"] = 3

    # KOF Specific
    default_env_settings["fighting_style"] = 0
    default_env_settings["ultimate_style"] = (0, 0, 0)

    default_env_settings["hardcore"] = False
    default_env_settings["disable_keyboard"] = True
    default_env_settings["disable_joystick"] = True
    default_env_settings["rank"] = 0
    default_env_settings["seed"] = -1
    default_env_settings["grpc_timeout"] = 60

    # User settings
    for k, v in env_settings.items():

        # Check for characters
        if k == "characters":
            for ichar in range(len(v), max_char_to_select):
                v + ("Random",)

        default_env_settings[k] = v

    keys_2p = ["characters", "char_outfits", "action_space", "attack_but_combination",
               "super_art", "fighting_style", "ultimate_style"]

    for key in keys_2p:
        if default_env_settings["player"] != "P1P2":
            if type(default_env_settings[key]) == list:
                warning_message  = "\"{}\" value should not be a list when using 1P environments, ".format(key)
                warning_message += "discarding the second element."
                logger.warning(warning_message)
                value_to_copy = default_env_settings[key][0]
            else:
                value_to_copy = default_env_settings[key]
        else:
            if type(default_env_settings[key]) != list:
                warning_message  = "\"{}\" value should be a 2 elements list when using 2P environments, ".format(key)
                warning_message += "duplicating the provided one."
                logger.warning(warning_message)
                value_to_copy = default_env_settings[key]

        default_env_settings[key] = [value_to_copy,
                                     value_to_copy]

    return default_env_settings


def make(game_id, env_settings={}, wrappers_settings={},
         traj_rec_settings={}, seed=None, rank=0, log_level=logging.INFO):
    """
    Create a wrapped environment.
    :param seed: (int) the initial seed for RNG
    :param wrappers_settings: (dict) the parameters for envWrapping function
    :param log_level: (int) the logging level (e.g logging.DEBUG)
    """

    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)

    # Include game_id in env_settings
    env_settings["game_id"] = game_id

    # Check if DIAMBRA_ENVS var present
    env_addresses = os.getenv("DIAMBRA_ENVS", "").split()
    if len(env_addresses) >= 1:  # If present
        # Check if there are at least n env_addresses as the prescribed rank
        if len(env_addresses) < rank + 1:
            raise Exception("Rank of env client is higher than the available env_addresses servers:",
            "# of env servers: {}".format(len(env_addresses)),
            "# rank of client: {} (0-based index)".format(rank))
    else:  # If not present, set default value
        if "env_address" not in env_settings:
            env_addresses = ["localhost:50051"]
        else:
            env_addresses = [env_settings["env_address"]]

    env_settings["env_address"] = env_addresses[rank]
    env_settings["rank"] = rank
    if seed is not None:
        env_settings["seed"] = seed

    # Checking settings and setting up default ones
    env_settings = env_settings_check(env_settings, logger)

    # Make environment
    if env_settings["player"] != "P1P2":  # 1P Mode
        if env_settings["hardcore"] is True:
            env = DiambraGymHardcore1P(env_settings)
        else:
            env = DiambraGym1P(env_settings)
    else:  # 2P Mode
        if env_settings["hardcore"] is True:
            env = DiambraGymHardcore2P(env_settings)
        else:
            env = DiambraGym2P(env_settings)

    # Apply environment wrappers
    env = env_wrapping(env, env_settings["player"], **wrappers_settings,
                       hardcore=env_settings["hardcore"])

    # Apply trajectories recorder wrappers
    if traj_rec_settings is True:
        if env_settings["hardcore"]:
            from diambra.arena.wrappers.traj_rec_wrapper_hardcore import TrajectoryRecorder
        else:
            from diambra.arena.wrappers.traj_rec_wrapper import TrajectoryRecorder

        env = TrajectoryRecorder(env, **traj_rec_settings)

    return env
