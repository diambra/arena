import os
import logging
from dacite import from_dict
from .arena_gym import DiambraGymHardcore1P, DiambraGym1P, DiambraGymHardcore2P, DiambraGym2P
from .wrappers.arena_wrappers import env_wrapping
from .env_settings import EnvironmentSettings1P, EnvironmentSettings2P, WrappersSettings, RecordingSettings

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
    if "player" in env_settings.keys() and env_settings["player"] == "P1P2":
        env_settings = from_dict(EnvironmentSettings2P, env_settings)
    else:
        env_settings = from_dict(EnvironmentSettings1P, env_settings)
    env_settings.sanity_check()

    # Make environment
    if env_settings.player != "P1P2":  # 1P Mode
        if env_settings.hardcore is True:
            env = DiambraGymHardcore1P(env_settings)
        else:
            env = DiambraGym1P(env_settings)
    else:  # 2P Mode
        if env_settings.hardcore is True:
            env = DiambraGymHardcore2P(env_settings)
        else:
            env = DiambraGym2P(env_settings)

    # Apply environment wrappers
    wrappers_settings = from_dict(WrappersSettings, wrappers_settings)
    wrappers_settings.sanity_check()
    env = env_wrapping(env, wrappers_settings, hardcore=env_settings.hardcore)

    # Apply trajectories recorder wrappers
    if len(traj_rec_settings) != 0:
        traj_rec_settings = from_dict(RecordingSettings, traj_rec_settings)
        if env_settings.hardcore is True:
            from diambra.arena.wrappers.traj_rec_wrapper_hardcore import TrajectoryRecorder
        else:
            from diambra.arena.wrappers.traj_rec_wrapper import TrajectoryRecorder

        env = TrajectoryRecorder(env, traj_rec_settings)

    return env
