import os
import logging
from dacite import from_dict
from diambra.arena.arena_gym import DiambraGym1P, DiambraGym2P
from diambra.arena.wrappers.arena_wrappers import env_wrapping
from diambra.arena.env_settings import EnvironmentSettings1P, EnvironmentSettings2P, WrappersSettings, RecordingSettings
from diambra.arena.wrappers.episode_recording import EpisodeRecorder

def make(game_id, env_settings={}, wrappers_settings={}, episode_recording_settings={}, rank=0, log_level=logging.INFO):
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

    # Checking settings and setting up default ones
    if "n_players" in env_settings.keys() and env_settings["n_players"] == 2:
        env_settings = from_dict(EnvironmentSettings2P, env_settings)
    else:
        env_settings["n_players"] = 1
        env_settings = from_dict(EnvironmentSettings1P, env_settings)
    env_settings.sanity_check()

    # Make environment
    if env_settings.n_players == 1:  # 1P Mode
        env = DiambraGym1P(env_settings)
    else:  # 2P Mode
        env = DiambraGym2P(env_settings)

    # Apply episode recorder wrapper
    if len(episode_recording_settings) != 0:
        episode_recording_settings = from_dict(RecordingSettings, episode_recording_settings)
        env = EpisodeRecorder(env, episode_recording_settings)

    # Apply environment wrappers
    wrappers_settings = from_dict(WrappersSettings, wrappers_settings)
    wrappers_settings.sanity_check()
    env = env_wrapping(env, wrappers_settings)

    return env
