# Collection of policies to be applied on the environment
import numpy as np
import random

# No action policy


class noActionPolicy(object):

    def __init__(self, name="No Action", actionSpace="multiDiscrete"):
        self.id = "noAction"
        self.name = name
        self.actionSpace = actionSpace

    def initialize(self):
        pass

    def reset(self, observation):
        pass

    def act(self, observation, info=None):

        if self.actionSpace == "multiDiscrete":
            prob = [1.0, 1.0]
            action = [0, 0]
        else:
            prob = [1.0, 1.0]
            action = 0

        return action, prob

# Random policy, sampling from the action space


class randomPolicy(object):

    def __init__(self, nActions, name="Random", actionSpace="multiDiscrete"):
        self.nActions = np.array(nActions)
        self.id = "random"
        self.name = name
        self.actionSpace = actionSpace

    def initialize(self):
        pass

    def reset(self, observation):
        pass

    def act(self, observation, info=None):

        prob = 1.0/self.nActions

        if self.actionSpace == "discrete":
            action = random.randrange(self.nActions[0]+self.nActions[1]-1)
        else:
            action = []
            for idx in range(self.nActions.shape[0]):
                action.append(random.randrange(self.nActions[idx]))

        return action, prob

# RL Policy, which uses a model to select the action


class RLPolicy(object):

    def __init__(self, model, deterministicFlag,
                 nActions, name="Generic RL", actionSpace="multiDiscrete"):

        self.nActions = nActions
        self.deterministicFlag = deterministicFlag
        self.model = model
        self.id = "rl"
        self.name = name
        self.actionSpace = actionSpace

    def initialize(self):
        pass

    def reset(self, observation):
        pass

    def updateWeights(self, wPath):
        print("Loading new weights: {}".format(wPath))
        self.model.load_parameters(wPath)

    def act(self, observation, info=None):
        action_prob = self.model.action_probability(observation)

        # if self.deterministicFlag:
        #   action = np.argmax(action_prob)
        # else:
        #   if self.actionSpace == "discrete":
        #       action = np.random.choice([x for x in range(len(action_prob))],
        #                                 p=action_prob)
        #   else:
        #       action = self.model.predict(observation,
        #                                   deterministic=self.deterministicFlag)
        action, _ = self.model.predict(
            observation, deterministic=self.deterministicFlag)
        action = action.tolist()

        prob = action_prob
        if self.actionSpace == "discrete":

            if action >= self.nActions[0]:
                prob = [0.0, action_prob[action]]
            else:
                prob = [action_prob[action], 0.0]
        else:

            prob = action_prob
            # print("Warning!! Probabilities for
            #        MultiDiscrete are not correct!")
            # Can be ok doing nothing, but better to check
            # raise Exception("To be checked")

        return action, prob

# Human policy, retrieved via GamePad


class gamepadPolicy(object):

    def __init__(self, gamepadClass, name="Human"):
        self.gamePadClass = gamepadClass
        self.id = "gamepad"
        self.initialized = False
        self.name = name

    def initialize(self, actionList, gamepadNum=0):
        if not self.initialized:
            self.gamePad = self.gamePadClass(actionList=actionList,
                                             gamepadNum=gamepadNum)
            self.gamePad.start()
            self.initialized = True

    def reset(self, observation):
        pass

    def getActions(self):
        return self.gamePad.getActions()

    def act(self, observation, info=None):

        prob = [1.0, 1.0]
        action = self.gamePad.getActions()

        return action, prob
