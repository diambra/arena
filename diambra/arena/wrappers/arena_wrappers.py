import random
import numpy as np
import gymnasium as gym
import logging
from diambra.arena import SpaceTypes, WrappersSettings
from diambra.arena.wrappers.observation import WarpFrame, GrayscaleFrame, FrameStack, ActionsStack, \
                                               NormalizeObservation, FlattenFilterDictObs, \
                                               AddLastActionToObservation, RoleRelativeObservation

# Remove attack buttons combinations
class NoAttackButtonsCombinations(gym.Wrapper):
    def __init__(self, env):
        """
        Limit attack actions to single buttons removing attack buttons combinations
        :param env: (Gym Environment) the environment to wrap
        """
        gym.Wrapper.__init__(self, env)
        # N actions
        self.n_actions = [self.unwrapped.env_info.available_actions.n_moves, self.unwrapped.env_info.available_actions.n_attacks_no_comb]
        if self.unwrapped.env_settings.n_players == 1:
            if self.unwrapped.env_settings.action_space == SpaceTypes.MULTI_DISCRETE:
                self.action_space = gym.spaces.MultiDiscrete(self.n_actions)
            elif self.unwrapped.env_settings.action_space == SpaceTypes.DISCRETE:
                self.action_space = gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
            else:
                raise Exception("Action space not recognized in \"NoAttackButtonsCombinations\" wrapper")
            self.unwrapped.logger.debug("Using {} action space without attack buttons combinations".format(SpaceTypes.Name(self.unwrapped.env_settings.action_space)))
        else:
            self.unwrapped.logger.warning("Warning: \"NoAttackButtonsCombinations\" is by default applied on all agents actions space")
            for idx in range(self.unwrapped.env_settings.n_players):
                if self.unwrapped.env_settings.action_space[idx] == SpaceTypes.MULTI_DISCRETE:
                    self.action_space["agent_{}".format(idx)] = gym.spaces.MultiDiscrete(self.n_actions)
                elif self.unwrapped.env_settings.action_space[idx] == SpaceTypes.DISCRETE:
                    self.action_space["agent_{}".format(idx)] = gym.spaces.Discrete(self.n_actions[0] + self.n_actions[1] - 1)
                else:
                    raise Exception("Action space not recognized in \"NoAttackButtonsCombinations\" wrapper")
                self.unwrapped.logger.debug("Using {} action space for agent_{} without attack buttons combinations".format(SpaceTypes.Name(self.unwrapped.env_settings.action_space[idx]), idx))

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)

    def step(self, action):
        return self.env.step(action)

class NoopReset(gym.Wrapper):
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
            obs, _, done, _ = self.env.step(self.unwrapped.get_no_op_action())
            if done:
                obs = self.env.reset(**kwargs)
        return obs

    def step(self, action):
        return self.env.step(action)

class StickyActions(gym.Wrapper):
    def __init__(self, env, sticky_actions):
        """
        Apply sticky actions
        :param env: (Gym Environment) the environment to wrap
        :param sticky_actions: (int) number of steps
               during which the same action is sent
        """
        gym.Wrapper.__init__(self, env)
        self.sticky_actions = sticky_actions
        assert self.unwrapped.env_settings.step_ratio == 1, "StickyActions wrapper can be activated only "\
                                                            "when step_ratio is set equal to 1"

    def step(self, action):
        rew = 0.0
        for _ in range(self.sticky_actions):
            obs, rew_step, done, info = self.env.step(action)
            rew += rew_step
            if info["round_done"] is True:
                break

        return obs, rew, done, info

class ClipReward(gym.RewardWrapper):
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

class NormalizeReward(gym.RewardWrapper):
    def __init__(self, env, reward_normalization_factor):
        """
        Normalize the reward dividing it by the product of
        rewardNormalizationFactor multiplied by
        the maximum character health variation (max - min).
        :param env: (Gym Environment) the environment
        :param rewardNormalizationFactor: multiplication factor
        """
        gym.RewardWrapper.__init__(self, env)
        self.unwrapped.reward_normalization_value = reward_normalization_factor * self.unwrapped.max_delta_health

    def reward(self, reward):
        """
        Normalize reward dividing by reward normalization factor*max_delta_health
        :param reward: (float)
        """
        return float(reward) / float(self.unwrapped.reward_normalization_value)

# Environment Wrapping (rewards normalization, resizing, grayscaling, etc)
def env_wrapping(env, wrappers_settings: WrappersSettings):
    """
    Typical standard environment wrappers
    :param env: (Gym Environment) the diambra environment
    :param wrappers_settings: (WrappersSettings) settings for the wrappers
    :return: (Gym Environment) the wrapped diambra environment
    """
    logger = logging.getLogger(__name__)

    ### Generic wrappers(s)
    if wrappers_settings.no_op_max > 0:
        env = NoopReset(env, no_op_max=wrappers_settings.no_op_max)

    if wrappers_settings.repeat_action > 1:
        env = StickyActions(env, sticky_actions=wrappers_settings.repeat_action)

    ### Reward wrappers(s)
    if wrappers_settings.normalize_reward is True:
        env = NormalizeReward(env, wrappers_settings.normalization_factor)

    if wrappers_settings.clip_reward is True:
        env = ClipReward(env)

    ### Action space wrapper(s)
    if wrappers_settings.no_attack_buttons_combinations is True:
        env = NoAttackButtonsCombinations(env)

    ### Observation space wrappers(s)
    if wrappers_settings.frame_shape[2] == 1:
        if env.observation_space["frame"].shape[2] == 1:
            env.unwrapped.logger.warning("Warning: skipping grayscaling as the frame is already single channel.")
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

    # Stack #frameStack frames together
    if wrappers_settings.stack_frames > 1:
        env = FrameStack(env, wrappers_settings.stack_frames, wrappers_settings.dilation)

    # Add last action to observation
    if wrappers_settings.add_last_action:
        env = AddLastActionToObservation(env)

        # Stack #actionsStack actions together
        if wrappers_settings.stack_actions > 1:
            env = ActionsStack(env, wrappers_settings.stack_actions)

    # Scales observations normalizing them between 0.0 and 1.0
    if wrappers_settings.scale is True:
        env = NormalizeObservation(env, wrappers_settings.exclude_image_scaling, wrappers_settings.process_discrete_binary)

    # Convert base observation to role-relative observation
    if wrappers_settings.role_relative is True:
        env = RoleRelativeObservation(env)

    if wrappers_settings.flatten is True:
        env = FlattenFilterDictObs(env, wrappers_settings.filter_keys)

    # Apply all additional wrappers in sequence:
    for wrapper in wrappers_settings.wrappers:
        env = wrapper[0](env, **wrapper[1])

    return env
