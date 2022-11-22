import random
import numpy as np
import gym
import logging
from diambra.arena.env_settings import WrappersSettings

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
        no_op_action = [0, 0, 0, 0]
        if isinstance(self.action_space, gym.spaces.Discrete):
            no_op_action = 0
        for _ in range(no_ops):
            obs, _, done, _ = self.env.step(no_op_action)
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

        assert self.env.env_settings.step_ratio == 1, "sticky_actions can "\
                                                      "be activated only "\
                                                      "when stepRatio is "\
                                                      "set equal to 1"

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
        the maximum character health variadtion (max - min).
        :param env: (Gym Environment) the environment
        :param rewardNormalizationFactor: multiplication factor
        """
        gym.RewardWrapper.__init__(self, env)
        self.env.reward_normalization_value = reward_normalization_factor * self.env.max_delta_health

    def reward(self, reward):
        """
        Nomralize reward dividing by reward normalization factor*max_delta_health
        :param reward: (float)
        """
        return float(reward) / float(self.env.reward_normalization_value)

# Environment Wrapping (rewards normalization, resizing, grayscaling, etc)
def env_wrapping(env, wrappers_settings: WrappersSettings, hardcore: bool=False):
    """
    Typical standard environment wrappers
    :param env: (Gym Environment) the diambra environment
    :param no_op_max: (int) wrap the environment to perform
                    no_op_max no action steps at reset
    :param clipRewards: (bool) wrap the reward clipping wrapper
    :param rewardNormalization: (bool) if to activate reward noramlization
    :param rewardNormalizationFactor: (double) noramlization factor
                                      for reward normalization wrapper
    :param frameStack: (int) wrap the frame stacking wrapper
                       using #frameStack frames
    :param dilation (frame stacking): (int) stack one frame every
                                      #dilation frames, useful to assure
                                      action every step considering
                                      a dilated subset of previous frames
    :param actionsStack: (int) wrap the frame stacking wrapper
                         using #frameStack frames
    :param scale: (bool) wrap the scaling observation wrapper
    :param scaleMod: (int) them scaling method: 0->[0,1] 1->[-1,1]
    :return: (Gym Environment) the wrapped diambra environment
    """
    logger = logging.getLogger(__name__)

    if wrappers_settings.no_op_max > 0:
        env = NoopResetEnv(env, no_op_max=wrappers_settings.no_op_max)

    if wrappers_settings.sticky_actions > 1:
        env = StickyActionsEnv(env, sticky_actions=wrappers_settings.sticky_actions)

    if hardcore is True:
        from diambra.arena.wrappers.obs_wrapper_hardcore import WarpFrame,\
            WarpFrame3C, FrameStack, FrameStackDilated,\
            ScaledFloatObsNeg, ScaledFloatObs
    else:
        from diambra.arena.wrappers.obs_wrapper import WarpFrame, \
            WarpFrame3C, FrameStack, FrameStackDilated,\
            ActionsStack, ScaledFloatObsNeg, ScaledFloatObs, FlattenFilterDictObs

    if wrappers_settings.hwc_obs_resize[2] == 1:
        # Resizing observation from H x W x 3 to
        # hwObsResize[0] x hwObsResize[1] x 1
        env = WarpFrame(env, wrappers_settings.hwc_obs_resize)
    elif wrappers_settings.hwc_obs_resize[2] == 3:
        # Resizing observation from H x W x 3 to
        # hwObsResize[0] x hwObsResize[1] x hwObsResize[2]
        env = WarpFrame3C(env, wrappers_settings.hwc_obs_resize)

    # Normalize rewards
    if wrappers_settings.reward_normalization is True:
        env = NormalizeRewardEnv(env, wrappers_settings.reward_normalization_factor)

    # Clip rewards using sign function
    if wrappers_settings.clip_rewards is True:
        env = ClipRewardEnv(env)

    # Stack #frameStack frames together
    if wrappers_settings.frame_stack > 1:
        if wrappers_settings.dilation == 1:
            env = FrameStack(env, wrappers_settings.frame_stack)
        else:
            logger.debug("Using frame stacking with dilation = {}".format(wrappers_settings.dilation))
            env = FrameStackDilated(env, wrappers_settings.frame_stack, wrappers_settings.dilation)

    # Stack #actionsStack actions together
    if wrappers_settings.actions_stack > 1 and not hardcore:
        env = ActionsStack(env, wrappers_settings.actions_stack)

    # Scales observations normalizing them
    if wrappers_settings.scale is True:
        if wrappers_settings.scale_mod == 0:
            # Between 0.0 and 1.0
            if hardcore is False:
                env = ScaledFloatObs(env, wrappers_settings.exclude_image_scaling, wrappers_settings.process_discrete_binary)
            else:
                env = ScaledFloatObs(env)
        elif wrappers_settings.scale_mod == -1:
            # Between -1.0 and 1.0
            raise RuntimeError("Scaling between -1.0 and 1.0 currently not implemented")
            env = ScaledFloatObsNeg(env)
        else:
            raise ValueError("Scale mod must be either 0 or -1")

    if wrappers_settings.flatten is True:
        if hardcore is True:
            logger.warning("Dictionary observation flattening is valid only for not hardcore mode, skipping it.")
        else:
            env = FlattenFilterDictObs(env, wrappers_settings.filter_keys)

    return env
