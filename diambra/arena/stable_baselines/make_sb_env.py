import os
import diambra.arena
from .wrappers.add_obs_wrap import AdditionalObsToChannel
from .wrappers.p2_wrap import SelfPlayVsRL, VsHum, IntegratedSelfPlay

from stable_baselines import logger
from stable_baselines.bench import Monitor
from stable_baselines.common.misc_util import set_global_seeds
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv


def make_sb_env(seed: int, env_settings: dict, wrappers_settings: dict={},
                traj_rec_settings: dict={}, custom_wrappers: list=None,
                key_to_add: list=None, p2_mode: str=None, p2_policy=None,
                start_index: int=0, allow_early_resets: bool=True,
                start_method: str=None, no_vec: bool=False,
                use_subprocess: bool=False):
    """
    Create a wrapped, monitored VecEnv.
    :param seed: (int) initial seed for RNG
    :param env_settings: (dict) parameters for DIAMBRA environment
    :param wrappers_settings: (dict) parameters for environment
                              wraping function
    :param traj_rec_settings: (dict) parameters for environment recording
                            wraping function
    :param key_to_add: (list) ordered parameters for environment stable
                       baselines converter wraping function
    :param start_index: (int) start rank index
    :param allow_early_resets: (bool) allows early reset of the environment
    :param start_method: (str) method used to start the subprocesses.
                        See SubprocVecEnv doc for more information
    :param use_subprocess: (bool) Whether to use `SubprocVecEnv` or
                          `DummyVecEnv` when
    :param no_vec: (bool) Whether to avoid usage of Vectorized Env or not.
                   Default: False
    :return: (VecEnv) The diambra environment
    """

    env_addresses = os.getenv("DIAMBRA_ENVS", "").split()
    if len(env_addresses) == 0:
        print("WARNING: running script without diambra CLI, this is a development option only.")
        env_addresses = ["0.0.0.0:50051"]

    num_envs = len(env_addresses)

    hardcore = False
    if "hardcore" in env_settings:
        hardcore = env_settings["hardcore"]

    def _make_sb_env(rank):
        def _thunk():
            env = diambra.arena.make(env_settings["game_id"], env_settings,
                                     wrappers_settings, traj_rec_settings,
                                     seed=seed + rank, rank=rank)
            if not hardcore:

                # Applying custom wrappers
                if custom_wrappers is not None:
                    for wrap in custom_wrappers:
                        env = wrap(env)

                env = AdditionalObsToChannel(env, key_to_add)
            if p2_mode is not None:
                if p2_mode == "integratedSelfPlay":
                    env = IntegratedSelfPlay(env)
                elif p2_mode == "selfPlayVsRL":
                    env = SelfPlayVsRL(env, p2_policy)
                elif p2_mode == "vsHum":
                    env = VsHum(env, p2_policy)

            env = Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)),
                          allow_early_resets=allow_early_resets)
            return env
        return _thunk
    set_global_seeds(seed)

    # If not wanting vectorized envs
    if no_vec and num_envs == 1:
        return _make_sb_env(0)(), num_envs

    # When using one environment, no need to start subprocesses
    if num_envs == 1 or not use_subprocess:
        return DummyVecEnv([_make_sb_env(i + start_index) for i in range(num_envs)]), num_envs

    return SubprocVecEnv([_make_sb_env(i + start_index) for i in range(num_envs)],
                         start_method=start_method), num_envs
