# Diambra Arena

from __future__ import annotations

import os
import warnings
from typing import Any, Callable, Dict

import cv2
import gymnasium as gym
import hydra
import numpy as np
from sheeprl.envs.wrappers import (
    FrameStack,
    GrayscaleRenderWrapper,
    RewardAsObservationWrapper,
)


def make_sheeprl_env(
    cfg: Dict[str, Any],
    seed: int,
    rank: int,
    run_name: str | None = None,
    prefix: str = "",
    vector_env_idx: int = 0,
) -> Callable[[], gym.Env]:
    """
    Create the callable function to create environment and
    force the environment to return an observation space of type
    gymnasium.spaces.Dict.

    Args:
        cfg (Dict[str, Any]): the configs of the environment to initialize.
        seed (int): the seed to use.
        rank (int): the rank of the process.
        run_name (str, optional): the name of the run.
            Default to None.
        prefix (str): the prefix to add to the video folder.
            Default to "".
        vector_env_idx (int): the index of the environment.

    Returns:
        The callable function that initializes the environment.
    """

    def thunk() -> gym.Env:
        if "diambra" in cfg.env.wrapper._target_ and not cfg.env.sync_env:
            if cfg.env.wrapper.diambra_settings.pop("splash_screen", True):
                warnings.warn(
                    "You must set the `splash_screen` setting to `False` when using the `AsyncVectorEnv` "
                    "in `DIAMBRA` environments. The specified `splash_screen` setting is ignored and set "
                    "to `False`."
                )
            cfg.env.wrapper.diambra_settings.splash_screen = False

        instantiate_kwargs = {}
        if "seed" in cfg.env.wrapper:
            instantiate_kwargs["seed"] = seed
        if "rank" in cfg.env.wrapper:
            instantiate_kwargs["rank"] = rank + vector_env_idx
        env = hydra.utils.instantiate(cfg.env.wrapper, **instantiate_kwargs)

        env_cnn_keys = set(
            [
                k
                for k in env.observation_space.spaces.keys()
                if len(env.observation_space[k].shape) in {2, 3}
            ]
        )
        if cfg.cnn_keys.encoder is None:
            user_cnn_keys = set()
        else:
            user_cnn_keys = set(cfg.cnn_keys.encoder)
        cnn_keys = env_cnn_keys.intersection(user_cnn_keys)

        def transform_obs(obs: Dict[str, Any]):
            for k in cnn_keys:
                current_obs = obs[k]
                shape = current_obs.shape
                is_3d = len(shape) == 3
                is_grayscale = not is_3d or shape[0] == 1 or shape[-1] == 1
                channel_first = not is_3d or shape[0] in (1, 3)

                # to 3D image
                if not is_3d:
                    current_obs = np.expand_dims(current_obs, axis=0)

                # channel last (opencv needs it)
                if channel_first:
                    current_obs = np.transpose(current_obs, (1, 2, 0))

                # resize
                if current_obs.shape[:-1] != (cfg.env.screen_size, cfg.env.screen_size):
                    current_obs = cv2.resize(
                        current_obs,
                        (cfg.env.screen_size, cfg.env.screen_size),
                        interpolation=cv2.INTER_AREA,
                    )

                # to grayscale
                if cfg.env.grayscale and not is_grayscale:
                    current_obs = cv2.cvtColor(current_obs, cv2.COLOR_RGB2GRAY)

                # back to 3D
                if len(current_obs.shape) == 2:
                    current_obs = np.expand_dims(current_obs, axis=-1)
                    if not cfg.env.grayscale:
                        current_obs = np.repeat(current_obs, 3, axis=-1)

                # channel first (PyTorch default)
                obs[k] = current_obs.transpose(2, 0, 1)

            return obs

        env = gym.wrappers.TransformObservation(env, transform_obs)
        for k in cnn_keys:
            env.observation_space[k] = gym.spaces.Box(
                0,
                255,
                (
                    1 if cfg.env.grayscale else 3,
                    cfg.env.screen_size,
                    cfg.env.screen_size,
                ),
                np.uint8,
            )

        if cnn_keys is not None and len(cnn_keys) > 0 and cfg.env.frame_stack > 1:
            if cfg.env.frame_stack_dilation <= 0:
                raise ValueError(
                    f"The frame stack dilation argument must be greater than zero, got: {cfg.env.frame_stack_dilation}"
                )
            env = FrameStack(
                env, cfg.env.frame_stack, cnn_keys, cfg.env.frame_stack_dilation
            )

        if cfg.env.reward_as_observation:
            env = RewardAsObservationWrapper(env)

        env.action_space.seed(seed)
        env.observation_space.seed(seed)
        if cfg.env.max_episode_steps and cfg.env.max_episode_steps > 0:
            env = gym.wrappers.TimeLimit(
                env, max_episode_steps=cfg.env.max_episode_steps
            )
        env = gym.wrappers.RecordEpisodeStatistics(env)
        if (
            cfg.env.capture_video
            and rank == 0
            and vector_env_idx == 0
            and run_name is not None
        ):
            if cfg.env.grayscale:
                env = GrayscaleRenderWrapper(env)
            env = gym.experimental.wrappers.RecordVideoV0(
                env,
                os.path.join(run_name, prefix + "_videos" if prefix else "videos"),
                disable_logger=True,
            )
            env.metadata["render_fps"] = env.frames_per_sec
        return env

    return thunk
