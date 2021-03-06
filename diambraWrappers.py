import sys, os, time, random
import numpy as np
from collections import deque
import cv2  # pytype:disable=import-error
cv2.ocl.setUseOpenCL(False)
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))

import gym
from gym import spaces

from diambraGym import *

import datetime
from parallelPickle import parallelPickleWriter

class NoopResetEnv(gym.Wrapper):
    def __init__(self, env, noop_max=6):
        """
        Sample initial states by taking random number of no-ops on reset.
        No-op is assumed to be first action (0).
        :param env: (Gym Environment) the environment to wrap
        :param noop_max: (int) the maximum value of no-ops to run
        """
        gym.Wrapper.__init__(self, env)
        self.noop_max = noop_max
        self.override_num_noops = None

    def reset(self, **kwargs):
        self.env.reset(**kwargs)
        if self.override_num_noops is not None:
            noops = self.override_num_noops
        else:
            noops = random.randint(1, self.noop_max + 1)
        assert noops > 0
        obs = None
        noopAction = [0, 0, 0, 0]
        if self.env.actionSpace[0] == "discrete" and self.env.playersNum != "2P":
            noopAction = 0
        for _ in range(noops):
            obs, _, done, _ = self.env.step(noopAction)
            if done:
                obs = self.env.reset(**kwargs)
        return obs

    def step(self, action):
        return self.env.step(action)

class MaxAndSkipEnv(gym.Wrapper):
    def __init__(self, env, skip=4):
        """
        Return only every `skip`-th frame (frameskipping)
        :param env: (Gym Environment) the environment
        :param skip: (int) number of `skip`-th frame
        """
        gym.Wrapper.__init__(self, env)
        # most recent raw observations (for max pooling across time steps)
        self._obs_buffer = np.zeros((2,)+env.observation_space.shape, dtype=env.observation_space.dtype)
        self._skip = skip

    def step(self, action):
        """
        Step the environment with the given action
        Repeat action, sum reward, and max over last observations.
        :param action: ([int] or [float]) the action
        :return: ([int] or [float], [float], [bool], dict) observation, reward, done, information
        """
        total_reward = 0.0
        done = None
        for i in range(self._skip):
            obs, reward, done, info = self.env.step(action)
            if i == self._skip - 2:
                self._obs_buffer[0] = obs
            if i == self._skip - 1:
                self._obs_buffer[1] = obs
            total_reward += reward
            if done:
                break
        # Note that the observation on the done=True frame
        # doesn't matter
        max_frame = self._obs_buffer.max(axis=0)

        return max_frame, total_reward, done, info

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)

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
        Normalize the reward dividing by the 50% of the maximum character health.
        :param env: (Gym Environment) the environment
        """
        gym.RewardWrapper.__init__(self, env)

    def reward(self, reward):
        """
        Nomralize reward dividing by reward normalization factor*max_health.
        :param reward: (float)
        """
        return float(reward)/float(self.env.rewNormFac*self.env.max_health)


class WarpFrame(gym.ObservationWrapper):
    def __init__(self, env, hw_obs_resize = [84, 84]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        gym.ObservationWrapper.__init__(self, env)
        self.width = hw_obs_resize[1]
        self.height = hw_obs_resize[0]
        self.observation_space = spaces.Box(low=0, high=255, shape=(self.height, self.width, 1),
                                            dtype=env.observation_space.dtype)

    def observation(self, frame):
        """
        returns the current observation from a frame
        :param frame: ([int] or [float]) environment frame
        :return: ([int] or [float]) the observation
        """
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
        return frame[:, :, None]

class WarpFrame3C(gym.ObservationWrapper):
    def __init__(self, env, hw_obs_resize = [224, 224]):
        """
        Warp frames to 84x84 as done in the Nature paper and later work.
        :param env: (Gym Environment) the environment
        """
        gym.ObservationWrapper.__init__(self, env)
        self.width = hw_obs_resize[1]
        self.height = hw_obs_resize[0]
        self.observation_space = spaces.Box(low=0, high=255, shape=(self.height, self.width, 3),
                                            dtype=env.observation_space.dtype)

    def observation(self, frame):
        """
        returns the current observation from a frame
        :param frame: ([int] or [float]) environment frame
        :return: ([int] or [float]) the observation
        """
        frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
        return frame


class FrameStack(gym.Wrapper):
    def __init__(self, env, n_frames):
        """Stack n_frames last frames.
        Returns lazy array, which is much more memory efficient.
        See Also
        --------
        stable_baselines.common.atari_wrappers.LazyFrames
        :param env: (Gym Environment) the environment
        :param n_frames: (int) the number of frames to stack
        """
        gym.Wrapper.__init__(self, env)
        self.n_frames = n_frames
        self.frames = deque([], maxlen=n_frames)
        shp = env.observation_space.shape
        self.observation_space = spaces.Box(low=0, high=255, shape=(shp[0], shp[1], shp[2] * n_frames),
                                            dtype=env.observation_space.dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for _ in range(self.n_frames):
            self.frames.append(obs)
        return self._get_ob()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs)
        return self._get_ob(), reward, done, info

    def _get_ob(self):
        assert len(self.frames) == self.n_frames
        return LazyFrames(list(self.frames))


class FrameStackDilated(gym.Wrapper):
    def __init__(self, env, n_frames, dilation):
        """Stack n_frames last frames with dilation factor.
        Returns lazy array, which is much more memory efficient.
        See Also
        --------
        stable_baselines.common.atari_wrappers.LazyFrames
        :param env: (Gym Environment) the environment
        :param n_frames: (int) the number of frames to stack
        :param dilation: (int) the dilation factor
        """
        gym.Wrapper.__init__(self, env)
        self.n_frames = n_frames
        self.dilation = dilation
        self.frames = deque([], maxlen=n_frames*dilation) # Keeping all n_frames*dilation in memory,
                                                          # then extract the subset given by the dilation factor
        shp = env.observation_space.shape
        self.observation_space = spaces.Box(low=0, high=255, shape=(shp[0], shp[1], shp[2] * n_frames),
                                            dtype=env.observation_space.dtype)

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for _ in range(self.n_frames*self.dilation):
            self.frames.append(obs)
        return self._get_ob()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.frames.append(obs)
        return self._get_ob(), reward, done, info

    def _get_ob(self):
        frames_subset = list(self.frames)[self.dilation-1::self.dilation]
        assert len(frames_subset) == self.n_frames
        return LazyFrames(list(frames_subset))


class ScaledFloatFrameNeg(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=env.observation_space.shape, dtype=np.float32)

    def observation(self, observation):
        # careful! This undoes the memory optimization, use
        # with smaller replay buffers only.
        return (np.array(observation).astype(np.float32) / 127.5) - 1.0

class ScaledFloatFrame(gym.ObservationWrapper):
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)
        self.observation_space = spaces.Box(low=0, high=1.0, shape=env.observation_space.shape, dtype=np.float32)

    def observation(self, observation):
        # careful! This undoes the memory optimization, use
        # with smaller replay buffers only.
        return np.array(observation).astype(np.float32) / 255.0


class LazyFrames(object):
    def __init__(self, frames):
        """
        This object ensures that common frames between the observations are only stored once.
        It exists purely to optimize memory usage which can be huge for DQN's 1M frames replay
        buffers.
        This object should only be converted to np.ndarray before being passed to the model.
        :param frames: ([int] or [float]) environment frames
        """
        self._frames = frames
        self._out = None

    def _force(self):
        if self._out is None:
            self._out = np.concatenate(self._frames, axis=2)
            self._frames = None
        return self._out

    def __array__(self, dtype=None):
        out = self._force()
        if dtype is not None:
            out = out.astype(dtype)
        return out

    def __len__(self):
        return len(self._force())

    def __getitem__(self, i):
        return self._force()[i]


def make_diambra(diambraGame, env_id, diambra_kwargs, diambra_gym_kwargs):
    """
    Create a wrapped diambra Environment
    :param env_id: (str) the environment ID
    :return: (Gym Environment) the wrapped diambra environment
    """

    env = diambraGame(env_id, diambra_kwargs, **diambra_gym_kwargs)
    env = NoopResetEnv(env, noop_max=6)
    #env = MaxAndSkipEnv(env, skip=4)
    return env

# Deepmind env processing (rewards normalization, resizing, grayscaling, etc)
def wrap_deepmind(env, clip_rewards=True, normalize_rewards=False, frame_stack=1,
                  scale=False, scale_mod = 0, hwc_obs_resize = [84, 84, 1], dilation=1):
    """
    Configure environment for DeepMind-style Atari.
    :param env: (Gym Environment) the diambra environment
    :param clip_rewards: (bool) wrap the reward clipping wrapper
    :param normalize_rewards: (bool) wrap the reward normalizing wrapper
    :param frame_stack: (int) wrap the frame stacking wrapper using #frame_stack frames
    :param dilation (frame stacking): (int) stack one frame every #dilation frames, useful
                                            to assure action every step considering a dilated
                                            subset of previous frames
    :param scale: (bool) wrap the scaling observation wrapper
    :return: (Gym Environment) the wrapped diambra environment
    """

    if hwc_obs_resize[2] == 1:
       # Resizing observation from H x W x 3 to hw_obs_resize[0] x hw_obs_resize[1] x 1
       env = WarpFrame(env, hwc_obs_resize)
    elif hwc_obs_resize[2] == 3:
       # Resizing observation from H x W x 3 to hw_obs_resize[0] x hw_obs_resize[1] x hw_obs_resize[2]
       env = WarpFrame3C(env, hwc_obs_resize)
    else:
       raise ValueError("Number of channel must be either 3 or 1")

    # Normalize rewards
    if normalize_rewards:
       env = NormalizeRewardEnv(env)

    # Clip rewards using sign function
    if clip_rewards:
        env = ClipRewardEnv(env)

    # Stack #frame_stack frames together
    if frame_stack > 1:
        if dilation == 1:
            env = FrameStack(env, frame_stack)
        else:
            print("Using frame stacking with dilation = {}".format(dilation))
            env = FrameStackDilated(env, frame_stack, dilation)

    # Scales observations normalizing them
    if scale:
        if scale_mod == 0:
           # Between 0.0 and 1.0
           env = ScaledFloatFrame(env)
        elif scale_mod == -1:
           # Between -1.0 and 1.0
           env = ScaledFloatFrameNeg(env)
        else:
           raise ValueError("Scale mod musto be either 0 or -1")

    return env

# Diambra additional observations (previous moves, character side, ecc)
class AddObs(gym.Wrapper):
    def __init__(self, env, key_to_add):
        """
        Add to observations additional info requested via `key_to_add` str list
        :param env: (Gym Environment) the environment to wrap
        :param key_to_add: (list of str) list of info to add to the observation
        """
        gym.Wrapper.__init__(self, env)
        self.key_to_add = key_to_add
        shp = self.env.observation_space.shape

        self.boxHighBound = self.env.observation_space.high.max()
        self.boxLowBound = self.env.observation_space.low.min()
        assert (self.boxHighBound == 1.0 or self.boxHighBound == 255),\
                "Observation space max bound must be either 1.0 or 255 to use Additional Obs"
        assert (self.boxLowBound == 0.0 or self.boxLowBound == -1.0),\
                "Observation space min bound must be either 0.0 or -1.0 to use Additional Obs"

        self.observation_space = spaces.Box(low=self.boxLowBound, high=self.boxHighBound,
                                            shape=(shp[0], shp[1], shp[2] + 1),
                                            dtype=np.float32)

        self.resetInfo = {}
        self.resetInfo["ownActionsBuf"] = np.concatenate(
                                           (self.actionsVector([0 for i in range(self.env.actBufLen)],
                                                               self.env.n_actions[0][0]),
                                            self.actionsVector([0 for i in range(self.env.actBufLen)],
                                                               self.env.n_actions[0][1]))
                                                      )
        self.resetInfo["oppActionsBuf"] = np.concatenate(
                                           (self.actionsVector([0 for i in range(self.env.actBufLen)],
                                                               self.env.n_actions[1][0]),
                                            self.actionsVector([0 for i in range(self.env.actBufLen)],
                                                               self.env.n_actions[1][1]))
                                                      )

        self.resetInfo["ownHealth"] = [1]
        self.resetInfo["oppHealth"] = [1]
        self.resetInfo["ownHealth_1"] = [1]
        self.resetInfo["ownHealth_2"] = [1]
        self.resetInfo["oppHealth_1"] = [1]
        self.resetInfo["oppHealth_2"] = [1]

        self.resetInfo["ownWins"] = [0]
        self.resetInfo["oppWins"] = [0]
        self.resetInfo["stage"] = [0.0]

    # Update playing char
    def updatePlayingChar(self, dictToUpdate, info):

        tmpChar1 = np.zeros(self.env.numberOfCharacters)
        tmpChar2 = np.zeros(self.env.numberOfCharacters)
        tmpChar1[info["ownCharacter"]] = 1
        if self.env.playersNum == "2P":
            tmpChar2[info["oppCharacter"]] = 1

        dictToUpdate["characters"] = np.concatenate( (tmpChar1, tmpChar2) )

        return

    # Building the one hot encoding actions vector
    def actionsVector(self, actionsBuf, nAct):

        actionsVector = np.zeros( (len(actionsBuf), nAct), dtype=int)

        for iAction, _ in enumerate(actionsBuf):
           actionsVector[iAction][actionsBuf[iAction]] = 1

        actionsVector = np.reshape(actionsVector, [-1])

        return actionsVector

    # Observation modification (adding one channel to store additional info)
    def observation_mod(self, obs, additionalInfo):

        shp = self.observation_space.shape

        # Adding a channel to the standard image, it will be in last position and it will store additional obs
        obsNew = np.zeros((shp[0], shp[1], shp[2]), dtype=self.env.observation_space.dtype)

        # Storing standard image in the first channel leaving the last one for additional obs
        obsNew[:,:,0:shp[2]-1] = obs

        # Creating the additional channel where to store new info
        obsNewAdd = np.zeros((shp[0], shp[1], 1), dtype=self.env.observation_space.dtype)

        # Adding new info to the additional channel, on a very long line and then reshaping into the obs dim
        newData = np.zeros((shp[0] * shp[1]))
        counter = 0
        for key in self.key_to_add:

           for addInfo in additionalInfo[key]:

              counter = counter + 1
              newData[counter] = addInfo

        newData[0] = counter
        newData = np.reshape(newData, (shp[0], -1))

        newData = newData * self.boxHighBound

        obsNew[:,:,shp[2]-1] = newData

        return obsNew

    # Creating dictionary for additional info of the step
    def to_step_info(self, info, action):

        step_info = {}
        step_info["ownActionsBuf"] = np.concatenate(
                                      (self.actionsVector( info["ownActionsBuf"][0], self.env.n_actions[0][0] ),
                                       self.actionsVector( info["ownActionsBuf"][1], self.env.n_actions[0][1] ))
                                                  )
        if self.playersNum == "2P":
            step_info["oppActionsBuf"] = np.concatenate(
                                          (self.actionsVector( info["oppActionsBuf"][0], self.env.n_actions[1][0] ),
                                           self.actionsVector( info["oppActionsBuf"][1], self.env.n_actions[1][1] ))
                                                      )

        if "ownHealth_1" not in self.key_to_add:
            step_info["ownHealth"] = [info["ownHealth"][0] / float(self.env.max_health)]
            step_info["oppHealth"] = [info["oppHealth"][0] / float(self.env.max_health)]
        else:
            step_info["ownHealth_1"] = [info["ownHealth"][0] / float(self.env.max_health)]
            step_info["ownHealth_2"] = [info["ownHealth"][1] / float(self.env.max_health)]
            step_info["oppHealth_1"] = [info["oppHealth"][0] / float(self.env.max_health)]
            step_info["oppHealth_2"] = [info["oppHealth"][1] / float(self.env.max_health)]

        step_info["ownPosition"] = [info["ownPosition"]]
        step_info["oppPosition"] = [info["oppPosition"]]

        step_info["ownWins"] = [info["ownWins"]]
        step_info["oppWins"] = [info["oppWins"]]

        step_info["stage"] = [ float(info["stage"] - 1) / float(self.env.max_stage - 1) ]

        self.updatePlayingChar(step_info, info)

        return step_info

    def reset(self, **kwargs):
        """
        Reset the environment and add requested info to the observation
        :return: new observation
        """

        obs = self.env.reset(**kwargs)
        obs = np.array(obs).astype(np.float32)

        info = self.env.envData.read_info()
        self.resetInfo["ownPosition"] = [info["ownPosition"]]
        self.resetInfo["oppPosition"] = [info["oppPosition"]]

        self.updatePlayingChar(self.resetInfo, info)

        obsNew = self.observation_mod(obs, self.resetInfo)

        # Store last observation
        self.env.lastObs = obsNew

        return obsNew

    def step(self, action):
        """
        Step the environment with the given action
        and add requested info to the observation
        :param action: ([int] or [float]) the action
        :return: new observation, reward, done, information
        """
        obs, reward, done, info = self.env.step(action)

        stepInfo = self.to_step_info(info, action)

        obsNew = self.observation_mod(obs, stepInfo)

        # Store last observation
        self.env.lastObs = obsNew

        return obsNew, reward, done, info

def additional_obs(env, key_to_add):
    """
    Add additional observations to the environment output.
    :param env: (Gym Environment) the diambra environment
    :param ket_to_add: (list of str) additional info to add to the obs
    :return: (Gym Environment) the wrapped diambra environment
    """

    if key_to_add != None:
       env = AddObs(env, key_to_add)

    return env

# Trajectory recorder wrapper
class TrajectoryRecorder(gym.Wrapper):
    def __init__(self, env, file_path, user_name, ignore_p2, commitHash, key_to_add):
        """
        Record trajectories to use them for imitation learning
        :param env: (Gym Environment) the environment to wrap
        :param filePath: (str) file path specifying where to store the trajectory file
        """
        gym.Wrapper.__init__(self, env)
        self.filePath = file_path
        self.userName = user_name
        self.ignoreP2 = ignore_p2
        self.key_to_add = key_to_add
        self.shp = self.env.observation_space.shape
        self.commitHash = commitHash

        if self.env.playersNum == "2P":
            if ((self.env.attackButCombinations[0] != self.env.attackButCombinations[1]) or\
                (self.env.actionSpace[0] != self.env.actionSpace[1])):
                raise Exception("Different attack buttons combinations and/or "\
                                "different action spaces not supported for 2P experience recordings")

        print("Recording trajectories in \"{}\"".format(self.filePath))
        os.makedirs(self.filePath, exist_ok = True)

    def reset(self, **kwargs):
        """
        Reset the environment and add requested info to the observation
        :return: observation
        """

        # Items to store
        self.lastFrameHist = []
        self.addObsHist = []
        self.rewardsHist = []
        self.actionsHist = []
        self.cumulativeRew = 0

        obs = self.env.reset(**kwargs)

        for idx in range(self.shp[2]-1):
            self.lastFrameHist.append(obs[:,:,idx])

        self.addObsHist.append(obs[:,:,self.shp[2]-1])

        return obs

    def step(self, action):
        """
        Step the environment with the given action
        and add requested info to the observation
        :param action: ([int] or [float]) the action
        :return: new observation, reward, done, information
        """

        obs, reward, done, info = self.env.step(action)

        self.lastFrameHist.append(obs[:,:,self.shp[2]-2])
        self.addObsHist.append(obs[:,:,self.shp[2]-1])
        self.rewardsHist.append(reward)
        self.actionsHist.append(action)
        self.cumulativeRew += reward

        if done:
            to_save = {}
            to_save["commitHash"]    = self.commitHash
            to_save["userName"]      = self.userName
            to_save["playersNum"]    = self.env.playersNum
            to_save["difficulty"]    = self.env.difficulty
            to_save["ignoreP2"]      = self.ignoreP2
            to_save["charNames"]     = self.env.charNames
            to_save["actBufLen"]     = self.env.actBufLen
            to_save["nActions"]      = self.env.n_actions[0]
            to_save["attackButComb"] = self.env.attackButCombinations[0]
            to_save["actionSpace"]   = self.env.actionSpace[0]
            to_save["epLen"]         = len(self.rewardsHist)
            to_save["cumRew"]        = self.cumulativeRew
            to_save["keyToAdd"]      = self.key_to_add
            to_save["frames"]        = self.lastFrameHist
            to_save["addObs"]        = self.addObsHist
            to_save["rewards"]       = self.rewardsHist
            to_save["actions"]       = self.actionsHist

            # Characters name
            chars = ""
            # If 2P mode
            if self.env.playersNum == "2P" and self.ignoreP2 == 0:
                chars += self.env.charNames[info["ownCharacter"]]
                chars += self.env.charNames[info["oppCharacter"]]
            # If 1P mode
            else:
                chars += self.env.charNames[info["ownCharacter"]]

            savePath = self.filePath + "_mod" + str(self.ignoreP2)  + self.env.playersNum + "_" + chars +\
                       "_diff" + str(self.env.difficulty)  + "_rew" + str(np.round(self.cumulativeRew, 3)) +\
                       "_" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            pickleWriter = parallelPickleWriter(savePath, to_save)
            pickleWriter.start()

        return obs, reward, done, info
