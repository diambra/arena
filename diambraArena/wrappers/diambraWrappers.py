import sys, os, time, random
import numpy as np
from collections import deque

import gym
from gym import spaces

class NoopResetEnv(gym.Wrapper):
    def __init__(self, env, noOpMax=6):
        """
        Sample initial states by taking random number of no-ops on reset.
        No-op is assumed to be first action (0).
        :param env: (Gym Environment) the environment to wrap
        :param noOpMax: (int) the maximum value of no-ops to run
        """
        gym.Wrapper.__init__(self, env)
        self.noOpMax = noOpMax
        self.overrideNumNoOps = None

    def reset(self, **kwargs):
        self.env.reset(**kwargs)
        if self.overrideNumNoOps is not None:
            noOps = self.overrideNumNoOps
        else:
            noOps = random.randint(1, self.noOpMax + 1)
        assert noOps > 0
        obs = None
        noopAction = [0, 0, 0, 0]
        if (self.env.actionSpace[0] == "discrete") and self.env.playerSide != "P1P2":
            noopAction = 0
        for _ in range(noOps):
            obs, _, done, _ = self.env.step(noopAction)
            if done:
                obs = self.env.reset(**kwargs)
        return obs

    def step(self, action):
        return self.env.step(action)

class StickyActionsEnv(gym.Wrapper):
    def __init__(self, env, stickyActions):
        """
        Apply sticky actions
        :param env: (Gym Environment) the environment to wrap
        :param stickyActions: (int) number of steps during which the same action is sent
        """
        gym.Wrapper.__init__(self, env)
        self.stickyActions = stickyActions

        assert self.env.envSettings["stepRatio"] == 1, "StickyActions can be activated "\
                                                       "only when stepRatio is set equal to 1"

    def step(self, action):

        rew = 0.0

        for _ in range(self.stickyActions):

            obs, rewStep, done, info = self.env.step(action)
            rew += rewStep
            if info["roundDone"] == True:
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
    def __init__(self, env):
        """
        Normalize the reward dividing by the 50% of the maximum character health variadtion (max - min).
        :param env: (Gym Environment) the environment
        """
        gym.RewardWrapper.__init__(self, env)

    def reward(self, reward):
        """
        Nomralize reward dividing by reward normalization factor*maxDeltaHealth.
        :param reward: (float)
        """
        return float(reward)/float(self.env.rewNormFac*self.env.maxDeltaHealth)

# Environment Wrapping (rewards normalization, resizing, grayscaling, etc)
def envWrapping(env, player, noOpMax=0, stickyActions=1, clipRewards=False,
                normalizeRewards=True, frameStack=1, actionsStack=1, scale=False,
                scaleMod = 0, hwcObsResize = [84, 84, 0], dilation=1, hardCore=False):
    """
    Typical standard environment wrappers
    :param env: (Gym Environment) the diambra environment
    :param player: player identification to discriminate between 1P and 2P games
    :param noOpMax: (int) wrap the environment to perform noOpMax no action steps at reset
    :param clipRewards: (bool) wrap the reward clipping wrapper
    :param normalizeRewards: (bool) wrap the reward normalizing wrapper
    :param frameStack: (int) wrap the frame stacking wrapper using #frameStack frames
    :param dilation (frame stacking): (int) stack one frame every #dilation frames, useful
                                            to assure action every step considering a dilated
                                            subset of previous frames
    :param actionsStack: (int) wrap the frame stacking wrapper using #frameStack frames
    :param scale: (bool) wrap the scaling observation wrapper
    :param scaleMod: (int) them scaling method: 0->[0,1] 1->[-1,1]
    :return: (Gym Environment) the wrapped diambra environment
    """

    if noOpMax > 0:
        env = NoopResetEnv(env, noOpMax=noOpMax)

    if stickyActions > 1:
        env = StickyActionsEnv(env, stickyActions=stickyActions)

    if hardCore:
        from diambraArena.wrappers.obsWrapperHardCore import WarpFrame, WarpFrame3C, FrameStack, FrameStackDilated,\
                                                             ScaledFloatObsNeg, ScaledFloatObs
    else:
        from diambraArena.wrappers.obsWrapper import WarpFrame, WarpFrame3C, FrameStack, FrameStackDilated,\
                                                     ActionsStack, ScaledFloatObsNeg, ScaledFloatObs

    if hwcObsResize[2] == 1:
       # Resizing observation from H x W x 3 to hwObsResize[0] x hwObsResize[1] x 1
       env = WarpFrame(env, hwcObsResize)
    elif hwcObsResize[2] == 3:
       # Resizing observation from H x W x 3 to hwObsResize[0] x hwObsResize[1] x hwObsResize[2]
       env = WarpFrame3C(env, hwcObsResize)

    # Normalize rewards
    if normalizeRewards:
       env = NormalizeRewardEnv(env)

    # Clip rewards using sign function
    if clipRewards:
        env = ClipRewardEnv(env)

    # Stack #frameStack frames together
    if frameStack > 1:
        if dilation == 1:
            env = FrameStack(env, frameStack)
        else:
            print("Using frame stacking with dilation = {}".format(dilation))
            env = FrameStackDilated(env, frameStack, dilation)

    # Stack #actionsStack actions together
    if actionsStack > 1 and not hardCore:
        if player != "P1P2":
            env = ActionsStack(env, actionsStack)
        else:
            env = ActionsStack(env, actionsStack, nPlayers=2)

    # Scales observations normalizing them
    if scale:
        if scaleMod == 0:
           # Between 0.0 and 1.0
           env = ScaledFloatObs(env)
        elif scaleMod == -1:
           # Between -1.0 and 1.0
           raise RuntimeError("Scaling between -1.0 and 1.0 currently not implemented")
           env = ScaledFloatObsNeg(env)
        else:
           raise ValueError("Scale mod musto be either 0 or -1")

    return env
