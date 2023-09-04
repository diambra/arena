import random
import numpy as np
import gymnasium as gym
import logging
from diambra.arena.env_settings import WrappersSettings
from diambra.arena.wrappers.observation import WarpFrame, GrayscaleFrame, FrameStack, ActionsStack, \
                                               ScaledFloatObsNeg, ScaledFloatObs, FlattenFilterDictObs

# Remove attack buttons combinations
class NoAttackButtonsCombinations(gym.Wrapper):
    def __init__(self, env):
        """
        Limit attack actions to single buttons removing attack buttons combinations
        :param env: (Gym Environment) the environment to wrap
        """
        gym.Wrapper.__init__(self, env)
        # N actions
        self.n_actions = [self.env_info.available_actions.n_moves, self.env_info.available_actions.n_attacks_no_comb]
        if self.env_settings.action_space == "multi_discrete":
            self.action_space = gym.spaces.MultiDiscrete(self.n_actions)
            self.logger.debug("Using MultiDiscrete action space without attack buttons combinations")
        elif self.env_settings.action_space == "discrete":
            self.action_space = gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
            self.logger.debug("Using Discrete action space without attack buttons combinations")

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)

    def step(self, action):
        return self.env.step(action)

class NoopResetEnv(gym.Wrapper):
    def __init__(self, env, no_op_max=6):
        """
        Sample initial states by taking random number of no-ops on reset.
        No-op is assumed to be first action (0).
        :param env: (Gym Environment) the environment to wrap
        :param no_op_max: (int) the maximum value of no-ops to run
        """
        gym.Wrapper.__init__(self, env)
        self.no_op_max = no_op_max
        self.override_num_no_ops = None

    def reset(self, **kwargs):
        self.env.reset(**kwargs)
        if self.override_num_no_ops is not None:
            no_ops = self.override_num_no_ops
        else:
            no_ops = random.randint(1, self.no_op_max + 1)
        assert no_ops > 0
        obs = None
        for _ in range(no_ops):
            obs, _, done, _ = self.env.step(self.env.get_no_op_action())
            if done:
                obs = self.env.reset(**kwargs)
        return obs

    def step(self, action):
        return self.env.step(action)

class StickyActionsEnv(gym.Wrapper):
    def __init__(self, env, sticky_actions):
        """
        Apply sticky actions
        :param env: (Gym Environment) the environment to wrap
        :param sticky_actions: (int) number of steps
               during which the same action is sent
        """
        gym.Wrapper.__init__(self, env)
        self.sticky_actions = sticky_actions
        assert self.env.env_settings.step_ratio == 1, "sticky_actions can be activated only "\
                                                      "when step_ratio is set equal to 1"

    def step(self, action):
        rew = 0.0
        for _ in range(self.sticky_actions):
            obs, rew_step, done, info = self.env.step(action)
            rew += rew_step
            if info["round_done"] is True:
                break

        return obs, rew, done, info

class ClipRewardEnv(gym.RewardWrapper):
    def __init__(self, env):
        """
        clips the reward to {+1, 0, -1} by its sign.
        :param env: (Gym Environment) the environment
        """
        gym.RewardWrapper.__init__(self, env)

    def reward(self, reward):
        """
        Bin reward to {+1, 0, -1} by its sign.
        :param reward: (float)
        """
        return np.sign(reward)


class NormalizeRewardEnv(gym.RewardWrapper):
    def __init__(self, env, reward_normalization_factor):
        """
        Normalize the reward dividing it by the product of
        rewardNormalizationFactor multiplied by
        the maximum character health variation (max - min).
        :param env: (Gym Environment) the environment
        :param rewardNormalizationFactor: multiplication factor
        """
        gym.RewardWrapper.__init__(self, env)
        self.env.reward_normalization_value = reward_normalization_factor * self.env.max_delta_health

    def reward(self, reward):
        """
        Normalize reward dividing by reward normalization factor*max_delta_health
        :param reward: (float)
        """
        return float(reward) / float(self.env.reward_normalization_value)

# Environment Wrapping (rewards normalization, resizing, grayscaling, etc)
def env_wrapping(env, wrappers_settings: WrappersSettings):
    """
    Typical standard environment wrappers
    :param env: (Gym Environment) the diambra environment
    :param wrappers_settings: (WrappersSettings) settings for the wrappers
    :return: (Gym Environment) the wrapped diambra environment
    """
    logger = logging.getLogger(__name__)

    if wrappers_settings.no_attack_buttons_combinations is True:
        env = NoAttackButtonsCombinations(env)

    if wrappers_settings.no_op_max > 0:
        env = NoopResetEnv(env, no_op_max=wrappers_settings.no_op_max)

    if wrappers_settings.sticky_actions > 1:
        env = StickyActionsEnv(env, sticky_actions=wrappers_settings.sticky_actions)

    if wrappers_settings.frame_shape[2] == 1:
        if env.observation_space["frame"].shape[2] == 1:
            env.logger.warning("Warning: skipping grayscaling as the frame is already single channel.")
        else:
            # Greyscaling frame to h x w x 1
            env = GrayscaleFrame(env)

    if wrappers_settings.frame_shape[0] != 0 and wrappers_settings.frame_shape[1] != 0:
        # Resizing observation from H x W x C to
        # frame_shape[0] x frame_shape[1] x C
        # Check if frame shape is bigger than native shape
        native_frame_size = env.observation_space["frame"].shape
        if wrappers_settings.frame_shape[0] > native_frame_size[0] or wrappers_settings.frame_shape[1] > native_frame_size[1]:
            warning_message  = "Warning: \"frame_shape\" greater than game native frame shape.\n"
            warning_message += "   \"native frame shape\" = [" + str(native_frame_size[0])
            warning_message += " X " + str(native_frame_size[1]) + "]\n"
            warning_message += "   \"frame_shape\" = [" + str(wrappers_settings.frame_shape[0])
            warning_message += " X " + str(wrappers_settings.frame_shape[1]) + "]"
            env.logger.warning(warning_message)

        env = WarpFrame(env, wrappers_settings.frame_shape[:2])

    # Normalize rewards
    if wrappers_settings.reward_normalization is True:
        env = NormalizeRewardEnv(env, wrappers_settings.reward_normalization_factor)

    # Clip rewards using sign function
    if wrappers_settings.clip_rewards is True:
        env = ClipRewardEnv(env)

    # Stack #frameStack frames together
    if wrappers_settings.frame_stack > 1:
        env = FrameStack(env, wrappers_settings.frame_stack, wrappers_settings.dilation)

    # Stack #actionsStack actions together
    if wrappers_settings.actions_stack > 1:
        env = ActionsStack(env, wrappers_settings.actions_stack)

    # Scales observations normalizing them
    if wrappers_settings.scale is True:
        if wrappers_settings.scale_mod == 0:
            # Between 0.0 and 1.0
            env = ScaledFloatObs(env, wrappers_settings.exclude_image_scaling, wrappers_settings.process_discrete_binary)
        elif wrappers_settings.scale_mod == -1:
            # Between -1.0 and 1.0
            raise RuntimeError("Scaling between -1.0 and 1.0 currently not implemented")
            env = ScaledFloatObsNeg(env)
        else:
            raise ValueError("Scale mod must be either 0 or -1")

    if wrappers_settings.flatten is True:
        env = FlattenFilterDictObs(env, wrappers_settings.filter_keys)

    # Apply all additional wrappers in sequence
    if wrappers_settings.additional_wrappers_list is not None:
        for wrapper in wrappers_settings.additional_wrappers_list:
            env = wrapper[0](env, **wrapper[1])

    return env
