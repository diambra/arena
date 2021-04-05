# Submitted agent

# All required imports here
import numpy as np
import random

# Observation modification function here (if any)
def observationModification(observation):

    return

# Additional model related function here (if any)

# Random agent, sampling from the action space
class agent(object):

    # Agent constructor
    def __init__(self, agentModel=None, nActions=[9, 4], name="Random Agent", actionSpace="multiDiscrete"):
        self.nActions = np.array(nActions)
        self.id = "random"
        self.name = name
        self.actionSpace = actionSpace

    # Optional method to initialize variables
    def initialize(self):
        pass

    # Action selection performed by the agent policy
    def act(self, observation):

        # Modify observation as you wish (only if you need to!
        # Keep in mind inference time constraints)
        observationModification(observation)

        # Random action selection
        if self.actionSpace == "discrete":
            action = random.randrange(self.nActions[0]+self.nActions[1]-1)
        else:
            action = []
            for idx in range(self.nActions.shape[0]):
                action.append(random.randrange(self.nActions[idx]))

        return action
