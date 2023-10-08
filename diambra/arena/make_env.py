import os
import logging
from diambra.arena.arena_gym import DiambraGym1P, DiambraGym2P
from diambra.arena.wrappers.arena_wrappers import env_wrapping
from diambra.arena import EnvironmentSettings, EnvironmentSettingsMultiAgent, WrappersSettings, RecordingSettings
from diambra.arena.wrappers.episode_recording import EpisodeRecorder
from typing import Union

def make(game_id, env_settings: Union[EnvironmentSettings, EnvironmentSettingsMultiAgent]=EnvironmentSettings(),
         wrappers_settings: WrappersSettings=WrappersSettings(), episode_recording_settings: RecordingSettings=RecordingSettings(),
         render_mode: str=None, rank: int=0, env_addresses=["localhost:50051"], log_level=logging.INFO):
    """
    Create a wrapped environment.
    :param seed: (int) the initial seed for RNG
    :param wrappers_settings: (dict) the parameters for envWrapping function
    :param log_level: (int) the logging level (e.g logging.DEBUG)
    """

    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)

    # Include game_id and render_mode in env_settings
    env_settings.game_id = game_id
    env_settings.render_mode = render_mode

    # Check if DIAMBRA_ENVS var present
    env_addresses_cli = os.getenv("DIAMBRA_ENVS", "").split()
    if len(env_addresses_cli) >= 1:  # If present
        # Check if there are at least n env_addresses as the prescribed rank
        if len(env_addresses_cli) < rank + 1:
            raise Exception("Rank of env client is higher than the available env_addresses servers:",
            "# of env servers: {}".format(len(env_addresses_cli)),
            "# rank of client: {} (0-based index)".format(rank))
        env_addresses_list = env_addresses_cli
    else:  # If not present, set default value
        env_addresses_list = env_addresses

    env_settings.env_address = env_addresses_list[rank]
    env_settings.rank = rank

    # Make environment
    if env_settings.n_players == 1:  # 1P Mode
        env = DiambraGym1P(env_settings)
    else:  # 2P Mode
        env = DiambraGym2P(env_settings)

    # Apply episode recorder wrapper
    if episode_recording_settings.dataset_path is not None:
        episode_recording_settings.sanity_check()
        env = EpisodeRecorder(env, episode_recording_settings)

    # Apply environment wrappers
    wrappers_settings.sanity_check()
    env = env_wrapping(env, wrappers_settings)

    return env
